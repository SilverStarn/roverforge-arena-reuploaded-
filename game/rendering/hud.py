"""Heads-up display widgets for the Panda3D app."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel
from panda3d.core import TextNode

from game.core.types import Observation
from game.rendering.theme import THEME, Color


MetricTile = tuple[str, str]
DebugLayerState = Mapping[str, bool]
HudAction = Callable[[], None]


def _noop() -> None:
    return None


@dataclass(frozen=True)
class HudCallbacks:
    toggle_autopilot: HudAction = _noop
    toggle_pause: HudAction = _noop
    step_once: HudAction = _noop
    toggle_camera: HudAction = _noop
    toggle_debug: HudAction = _noop
    reset: HudAction = _noop
    toggle_guide: HudAction = _noop
    toggle_sensors: HudAction = _noop
    toggle_bounds: HudAction = _noop
    toggle_path: HudAction = _noop
    toggle_events: HudAction = _noop


def format_progress_line(observation: Observation, target_count: int, max_steps: int) -> str:
    collected = target_count - int(observation["targets_remaining"])
    completion = float(observation["completion_ratio"]) * 100.0
    return (
        f"beacons {collected}/{target_count} | "
        f"steps {observation['step']}/{max_steps} | "
        f"complete {completion:.0f}%"
    )


def format_reward_breakdown(observation: Observation) -> str:
    breakdown = observation.get("last_reward_breakdown") or {}
    if not breakdown:
        return "step reward: waiting"

    return (
        "reward: "
        f"time {breakdown.get('time', 0.0):+.2f} | "
        f"progress {breakdown.get('progress', 0.0):+.2f} | "
        f"beacon {breakdown.get('target', 0.0):+.2f}\n"
        f"collision {breakdown.get('collision', 0.0):+.2f} | "
        f"finish {breakdown.get('success', 0.0):+.2f}"
    )


def format_native_badge(status: str) -> str:
    if "enabled" in status:
        return "c++ scorer"
    if "fallback" in status:
        return "python scorer"
    return "scorer"


def format_debug_mode(debug_layers: DebugLayerState) -> str:
    enabled_count = sum(1 for enabled in debug_layers.values() if enabled)
    if enabled_count == 0:
        return "off"
    if enabled_count == len(debug_layers):
        return "all on"
    return "mixed"


def format_button_label(name: str, value: str) -> str:
    return f"{name}: {value}" if value else name


def format_metric_tiles(
    observation: Observation,
    *,
    target_count: int,
    max_steps: int,
    total_reward: float,
) -> tuple[MetricTile, ...]:
    collected = target_count - int(observation["targets_remaining"])
    speed = float(observation.get("speed", 0.0))
    return (
        ("Score", f"{total_reward:+.2f}"),
        ("Beacons", f"{collected}/{target_count}"),
        ("Step", f"{observation['step']}/{max_steps}"),
        ("Speed", f"{speed:+.1f}"),
        ("Clearance", f"{float(observation['path_score']):.2f}"),
    )


def guide_text(agent_name: str) -> str:
    return (
        "Collect green beacons while avoiding crates and walls.\n"
        "Score rewards progress, beacons, and the finish bonus.\n"
        "Time and collisions reduce score.\n\n"
        "W/S drive    A/D steer    Tab auto\n"
        f"{agent_name} agent    P pause    C camera    F1-F5 debug"
    )


class ArenaHud:
    def __init__(self, callbacks: HudCallbacks | None = None) -> None:
        self.callbacks = callbacks or HudCallbacks()
        self.header_label = self._make_label(
            pos=(-1.29, 0, 0.91),
            frame_size=(-0.47, 0.50, -0.055, 0.065),
            text_scale=0.030,
            text_pos=(-0.445, -0.012),
            color=THEME.ui_panel,
            text_align=TextNode.ALeft,
        )
        self.progress_label = self._make_label(
            pos=(-1.34, 0, 0.80),
            frame_size=(-0.34, 0.50, -0.045, 0.045),
            text_scale=0.028,
            text_pos=(-0.315, -0.010),
            color=THEME.ui_panel_soft,
            text_align=TextNode.ALeft,
            text_fg=THEME.ui_muted,
        )
        self.metric_tiles = self._build_metric_tiles()
        self.collision_label = self._make_label(
            pos=(-1.34, 0, 0.37),
            frame_size=(-0.34, 0.50, -0.045, 0.045),
            text_scale=0.029,
            text_pos=(-0.315, -0.010),
            color=THEME.ui_panel_soft,
            text_align=TextNode.ALeft,
        )
        self.reward_breakdown_label = self._make_label(
            pos=(-1.34, 0, 0.255),
            frame_size=(-0.34, 0.50, -0.058, 0.058),
            text_scale=0.022,
            text_pos=(-0.315, 0.018),
            color=THEME.ui_panel_soft,
            text_align=TextNode.ALeft,
            text_fg=(0.94, 0.88, 0.66, 1.0),
        )
        self.reward_text = self._make_label(
            pos=(-1.34, 0, 0.12),
            frame_size=(-0.34, 0.50, -0.070, 0.070),
            text_scale=0.026,
            text_pos=(-0.315, 0.024),
            color=THEME.ui_panel_soft,
            text_align=TextNode.ALeft,
            text_fg=(0.88, 0.86, 0.68, 1.0),
        )
        self.summary_text = self._make_label(
            pos=(-1.34, 0, -0.06),
            frame_size=(-0.34, 0.50, -0.050, 0.050),
            text_scale=0.029,
            text_pos=(-0.315, -0.010),
            color=THEME.ui_panel_soft,
            text_align=TextNode.ALeft,
            text_fg=(0.80, 0.90, 1.0, 1.0),
        )
        self.control_buttons = self._build_control_buttons()
        self.debug_buttons = self._build_debug_buttons()
        self._build_guide_panel()

    def update(
        self,
        observation: Observation,
        *,
        mode: str,
        agent_name: str,
        seed: int,
        target_count: int,
        max_steps: int,
        camera_mode: str,
        total_reward: float,
        native_status: str,
        reward_feed: list[str],
        show_reward_feed: bool,
        debug_layers: DebugLayerState,
        autopilot: bool,
        paused: bool,
        guide_visible: bool,
        episode_summary: str = "",
    ) -> None:
        self.header_label["text"] = (
            "RoverForge Arena\n"
            f"{mode} | {agent_name} | seed {seed} | {camera_mode} | "
            f"{format_native_badge(native_status)}"
        )
        self.progress_label["text"] = format_progress_line(observation, target_count, max_steps)

        for widget, (label, value) in zip(
            self.metric_tiles,
            format_metric_tiles(
                observation,
                target_count=target_count,
                max_steps=max_steps,
                total_reward=total_reward,
            ),
        ):
            widget["text"] = f"{label}\n{value}"

        self.collision_label["text"] = f"collisions {observation['collisions']}"
        self.collision_label["frameColor"] = (
            THEME.ui_panel_danger if int(observation["collisions"]) else THEME.ui_panel_soft
        )
        self.reward_breakdown_label["text"] = format_reward_breakdown(observation)
        self.reward_text["text"] = self._format_reward_feed(reward_feed, show_reward_feed)
        if episode_summary:
            self.summary_text["text"] = episode_summary
            self.summary_text.show()
        else:
            self.summary_text["text"] = ""
            self.summary_text.hide()
        self.guide_body["text"] = guide_text(agent_name)
        if guide_visible:
            self.guide_frame.show()
        else:
            self.guide_frame.hide()
        self._update_control_buttons(autopilot, paused, camera_mode, guide_visible, debug_layers)
        self._update_debug_buttons(debug_layers)

    def _make_label(
        self,
        *,
        pos: tuple[float, float, float],
        frame_size: tuple[float, float, float, float],
        text_scale: float,
        text_pos: tuple[float, float],
        color: Color,
        text_align: int = TextNode.ACenter,
        text_fg: Color = THEME.ui_text,
    ) -> DirectLabel:
        return DirectLabel(
            relief=DGG.FLAT,
            frameColor=color,
            frameSize=frame_size,
            text="",
            text_fg=text_fg,
            text_align=text_align,
            text_pos=text_pos,
            text_scale=text_scale,
            pos=pos,
        )

    def _make_button(
        self,
        *,
        label: str,
        pos: tuple[float, float, float],
        command: HudAction,
        color: Color = THEME.ui_panel_soft,
    ) -> DirectButton:
        return DirectButton(
            relief=DGG.RIDGE,
            frameColor=color,
            borderWidth=(0.006, 0.006),
            frameSize=(-0.185, 0.185, -0.040, 0.040),
            text=label,
            text_fg=THEME.ui_text,
            text_align=TextNode.ACenter,
            text_scale=0.025,
            text_pos=(0, -0.010),
            command=command,
            pos=pos,
        )

    def _build_metric_tiles(self) -> list[DirectLabel]:
        positions = (
            (-1.49, 0, 0.68),
            (-1.18, 0, 0.68),
            (-0.87, 0, 0.68),
            (-1.335, 0, 0.53),
            (-1.025, 0, 0.53),
        )
        return [
            self._make_label(
                pos=pos,
                frame_size=(-0.135, 0.135, -0.060, 0.060),
                text_scale=0.027,
                text_pos=(0, -0.021),
                color=THEME.ui_panel_soft,
            )
            for pos in positions
        ]

    def _build_control_buttons(self) -> dict[str, DirectButton]:
        specs = (
            ("autopilot", "Auto: Manual", 0.87, self.callbacks.toggle_autopilot),
            ("pause", "Pause: On", 0.76, self.callbacks.toggle_pause),
            ("step", "Step", 0.65, self.callbacks.step_once),
            ("camera", "Camera: Chase", 0.54, self.callbacks.toggle_camera),
            ("guide", "Guide", 0.43, self.callbacks.toggle_guide),
            ("debug", "Debug: All On", 0.32, self.callbacks.toggle_debug),
            ("reset", "Reset", 0.21, self.callbacks.reset),
        )
        return {
            key: self._make_button(label=label, pos=(1.42, 0, z), command=command)
            for key, label, z, command in specs
        }

    def _build_debug_buttons(self) -> dict[str, DirectButton]:
        specs = (
            ("sensors", "Sensors: On", 0.04, self.callbacks.toggle_sensors),
            ("bounds", "Bounds: On", -0.07, self.callbacks.toggle_bounds),
            ("path", "Path: On", -0.18, self.callbacks.toggle_path),
            ("events", "Events: On", -0.29, self.callbacks.toggle_events),
        )
        return {
            key: self._make_button(label=label, pos=(1.42, 0, z), command=command)
            for key, label, z, command in specs
        }

    def _update_control_buttons(
        self,
        autopilot: bool,
        paused: bool,
        camera_mode: str,
        guide_visible: bool,
        debug_layers: DebugLayerState,
    ) -> None:
        self._set_button(
            self.control_buttons["autopilot"],
            format_button_label("Auto", "Planner" if autopilot else "Manual"),
            autopilot,
        )
        self._set_button(
            self.control_buttons["pause"],
            format_button_label("Pause", "On" if paused else "Run"),
            paused,
        )
        self._set_button(self.control_buttons["step"], format_button_label("Step", ""), False)
        self._set_button(
            self.control_buttons["camera"],
            format_button_label("Camera", camera_mode.title()),
            camera_mode == "overhead",
        )
        self._set_button(
            self.control_buttons["guide"],
            format_button_label("Guide", "Hide" if guide_visible else "Show"),
            guide_visible,
        )
        self._set_button(
            self.control_buttons["debug"],
            format_button_label("Debug", format_debug_mode(debug_layers).title()),
            format_debug_mode(debug_layers) != "off",
        )
        self._set_button(self.control_buttons["reset"], format_button_label("Reset", ""), False)

    def _update_debug_buttons(self, debug_layers: DebugLayerState) -> None:
        labels = {
            "sensors": "Sensors",
            "bounds": "Bounds",
            "path": "Path",
            "events": "Events",
        }
        for key, button in self.debug_buttons.items():
            enabled = bool(debug_layers[key])
            self._set_button(
                button,
                format_button_label(labels[key], "On" if enabled else "Off"),
                enabled,
            )

    def _set_button(self, button: DirectButton, label: str, active: bool) -> None:
        button["text"] = label
        button["frameColor"] = self._button_color(active)

    def _button_color(self, active: bool) -> Color:
        return THEME.ui_panel_active if active else THEME.ui_panel

    def _build_guide_panel(self) -> None:
        self.guide_frame = DirectFrame(
            relief=DGG.FLAT,
            frameColor=(0.018, 0.026, 0.030, 0.92),
            frameSize=(-0.62, 0.62, -0.29, 0.29),
            pos=(0.0, 0, 0.18),
        )
        self.guide_title = DirectLabel(
            parent=self.guide_frame,
            relief=None,
            text="RoverForge Arena",
            text_fg=THEME.ui_text,
            text_scale=0.045,
            text_pos=(0, -0.014),
            pos=(0, 0, 0.205),
        )
        self.guide_body = DirectLabel(
            parent=self.guide_frame,
            relief=None,
            text="",
            text_fg=THEME.ui_text,
            text_align=TextNode.ACenter,
            text_scale=0.031,
            text_pos=(0, 0.035),
            pos=(0, 0, 0.050),
        )
        self.guide_confirm_button = DirectButton(
            parent=self.guide_frame,
            relief=DGG.RIDGE,
            borderWidth=(0.007, 0.007),
            frameColor=THEME.ui_panel_positive,
            frameSize=(-0.16, 0.16, -0.045, 0.045),
            text="Got it",
            text_fg=THEME.ui_text,
            text_align=TextNode.ACenter,
            text_scale=0.030,
            text_pos=(0, -0.012),
            command=self.callbacks.toggle_guide,
            pos=(0, 0, -0.220),
        )

    def _format_reward_feed(self, reward_feed: list[str], show_reward_feed: bool) -> str:
        if not show_reward_feed:
            return "events hidden"
        if not reward_feed:
            return "events quiet"
        return "\n".join(reward_feed)
