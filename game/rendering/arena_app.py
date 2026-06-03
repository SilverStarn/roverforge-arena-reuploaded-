"""Panda3D front end for RoverForge Arena."""

from __future__ import annotations

import math

from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from panda3d.core import (
    AntialiasAttrib,
    AmbientLight,
    ClockObject,
    DirectionalLight,
    LineSegs,
    NodePath,
    PandaNode,
    Vec3,
    Vec4,
    WindowProperties,
)

from game.agents import make_agent
from game.agents.grid_planner import GridPlannerAgent
from game.core import ArenaConfig, RewardEvent, TrainingArenaEnv
from game.core.types import ActionCommand, Observation
from game.native import native_status
from game.rendering.debug_draw import (
    circle_outline,
    polyline,
    rectangle_outline,
    reward_marker as make_reward_marker,
)
from game.rendering.geometry import make_box, make_cylinder, make_grid
from game.rendering.hud import ArenaHud, HudCallbacks
from game.rendering.settings import (
    CameraMode,
    CameraSettings,
    DebugSettings,
    RewardMarkerState,
    VisualSettings,
    WindowSettings,
)
from game.rendering.theme import THEME, Color, apply_material


InputState = dict[str, bool]
AgentPose = tuple[float, float, float, float]


class ArenaApp(ShowBase):
    def __init__(self, seed: int = 7, autopilot: bool = False, agent_name: str = "planner"):
        super().__init__()
        self.window_settings = WindowSettings()
        self.camera_settings = CameraSettings()
        self.visual_settings = VisualSettings()
        self.seed = seed
        self.env = TrainingArenaEnv(ArenaConfig(seed=seed))
        self.agent_name = agent_name
        self.agent = make_agent(agent_name, self.env, seed=seed)
        self.autopilot = autopilot
        self.paused = not autopilot
        self.step_once = False
        self.guide_visible = True
        self.guide_pause = not autopilot
        self.camera_mode: CameraMode = "chase"
        self.debug = DebugSettings()
        self.accumulator = 0.0
        self.frame_dt = 0.0
        self.visual_time = 0.0
        self.wheel_rotation = 0.0
        self.collision_flash_timer = 0.0
        self.camera_ready = False
        self.last_observation = self.env.observe()
        self.previous_agent_pose = self._agent_pose()
        self.current_agent_pose = self.previous_agent_pose
        self.visual_agent_pose = self.current_agent_pose
        self.reward_feed: list[str] = []
        self.reward_markers: list[RewardMarkerState] = []
        self.episode_summary = ""
        self.episode_summary_ttl = 0.0
        self.keys: InputState = {
            "forward": False,
            "reverse": False,
            "left": False,
            "right": False,
        }

        self.level_root = self.render.attachNewNode("level")
        self.target_nodes: list[NodePath] = []
        self.target_visuals: list[dict[str, NodePath]] = []
        self.sensor_node: NodePath | None = None
        self.bounds_node: NodePath | None = None
        self.path_node: NodePath | None = None
        self.reward_node: NodePath | None = None
        self.rover = self.render.attachNewNode("rover")
        self.rover_colored_nodes: list[tuple[NodePath, Color]] = []
        self.wheel_nodes: list[NodePath] = []

        self._configure_window()
        self._build_lighting()
        self._build_level()
        self._build_rover()
        self._build_hud()
        self._bind_controls()

        self.disableMouse()
        self.taskMgr.add(self._update, "arena-update")

    def _configure_window(self) -> None:
        props = WindowProperties()
        props.setTitle(self.window_settings.title)
        props.setSize(self.window_settings.width, self.window_settings.height)
        self.win.requestProperties(props)
        self.setBackgroundColor(*self.window_settings.background_color)
        self.render.setShaderAuto()
        self.render.setAntialias(AntialiasAttrib.MAuto)

    def _build_lighting(self) -> None:
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.32, 0.35, 0.38, 1.0))
        self.render.setLight(self.render.attachNewNode(ambient))

        sun = DirectionalLight("sun")
        sun.setColor(Vec4(0.88, 0.86, 0.78, 1.0))
        sun_node = self.render.attachNewNode(sun)
        sun_node.setHpr(-35, -55, 0)
        self.render.setLight(sun_node)

        fill = DirectionalLight("fill")
        fill.setColor(Vec4(0.28, 0.36, 0.46, 1.0))
        fill_node = self.render.attachNewNode(fill)
        fill_node.setHpr(145, -25, 0)
        self.render.setLight(fill_node)

    def _build_level(self) -> None:
        self.level_root.removeNode()
        self.level_root = self.render.attachNewNode("level")
        self.target_nodes = []
        self.target_visuals = []

        self._build_floor()
        self._build_walls()
        self._build_obstacles()
        self._build_targets()

    def _build_floor(self) -> None:
        cfg = self.env.config
        floor = apply_material(
            make_box("floor", (cfg.width, cfg.depth, 0.08), THEME.floor),
            THEME.floor,
            shininess=8.0,
        )
        floor.reparentTo(self.level_root)
        floor.setZ(-0.08)

        panel_width = cfg.width / 4.0
        for index in range(4):
            panel = apply_material(
                make_box(
                    f"floor-panel-{index}",
                    (panel_width - 0.08, cfg.depth - 0.20, 0.012),
                    THEME.floor_panel,
                ),
                THEME.floor_panel,
                shininess=6.0,
            )
            panel.reparentTo(self.level_root)
            panel.setPos(-cfg.width / 2.0 + panel_width * (index + 0.5), 0, 0.012)

        make_grid("grid", cfg.width, cfg.depth, spacing=1.0, color=THEME.grid).reparentTo(
            self.level_root
        )

        start_pad = apply_material(
            make_box("start-pad", (2.2, 1.5, 0.026), THEME.start_pad),
            THEME.start_pad,
            shininess=14.0,
        )
        start_pad.reparentTo(self.level_root)
        start_pad.setPos(0, -cfg.depth / 2.0 + 1.8, 0.022)

        for offset in (-2.4, 2.4):
            lane = apply_material(
                make_box("lane-stripe", (0.07, cfg.depth - 1.2, 0.025), THEME.lane),
                THEME.lane,
                shininess=10.0,
            )
            lane.reparentTo(self.level_root)
            lane.setPos(offset, 0, 0.035)

    def _build_walls(self) -> None:
        cfg = self.env.config
        walls = (
            ((cfg.width + 0.4, 0.28, 0.75), (0, -cfg.depth / 2.0 - 0.14, 0)),
            ((cfg.width + 0.4, 0.28, 0.75), (0, cfg.depth / 2.0 + 0.14, 0)),
            ((0.28, cfg.depth, 0.75), (-cfg.width / 2.0 - 0.14, 0, 0)),
            ((0.28, cfg.depth, 0.75), (cfg.width / 2.0 + 0.14, 0, 0)),
        )
        for index, (size, pos) in enumerate(walls):
            wall = apply_material(make_box(f"wall-{index}", size, THEME.wall), THEME.wall)
            wall.reparentTo(self.level_root)
            wall.setPos(*pos)

            accent_size = (size[0], 0.055, 0.055) if size[0] > size[1] else (0.055, size[1], 0.055)
            rail = apply_material(
                make_box(f"wall-rail-{index}", accent_size, THEME.wall_accent),
                THEME.wall_accent,
                shininess=24.0,
            )
            rail.reparentTo(wall)
            rail.setPos(0, 0, 0.68)

        for x in (-cfg.width / 2.0 - 0.14, cfg.width / 2.0 + 0.14):
            for y in (-cfg.depth / 2.0 - 0.14, cfg.depth / 2.0 + 0.14):
                post = apply_material(
                    make_box("corner-post", (0.42, 0.42, 1.05), THEME.wall_accent),
                    THEME.wall_accent,
                    shininess=28.0,
                )
                post.reparentTo(self.level_root)
                post.setPos(x, y, 0)

    def _build_obstacles(self) -> None:
        for index, obstacle in enumerate(self.env.obstacles):
            root = self.level_root.attachNewNode(f"obstacle-root-{index}")
            root.setPos(obstacle.x, obstacle.y, 0)

            color = (
                THEME.obstacle[0],
                min(THEME.obstacle[1] + (index % 3) * 0.04, 1.0),
                THEME.obstacle[2],
                1.0,
            )
            body = apply_material(make_box(
                f"obstacle-{index}",
                (obstacle.width, obstacle.depth, obstacle.height),
                color,
            ), color)
            body.reparentTo(root)

            cap = apply_material(
                make_box(
                    f"obstacle-cap-{index}",
                    (obstacle.width + 0.08, obstacle.depth + 0.08, 0.06),
                    THEME.obstacle_cap,
                ),
                THEME.obstacle_cap,
                shininess=22.0,
            )
            cap.reparentTo(root)
            cap.setZ(obstacle.height)

            stripe = apply_material(
                make_box(
                    f"obstacle-stripe-{index}",
                    (max(obstacle.width * 0.72, 0.4), 0.055, 0.08),
                    THEME.obstacle_stripe,
                ),
                THEME.obstacle_stripe,
                shininess=26.0,
            )
            stripe.reparentTo(root)
            stripe.setPos(0, -obstacle.depth / 2.0 - 0.03, obstacle.height * 0.55)

    def _build_targets(self) -> None:
        for index, target in enumerate(self.env.targets):
            marker = self.level_root.attachNewNode(f"target-{index}")

            pad = apply_material(
                make_cylinder("target-pad", 0.62, 0.055, THEME.target_pad, segments=36),
                THEME.target_pad,
                shininess=18.0,
            )
            pad.reparentTo(marker)

            ring = apply_material(
                make_cylinder("target-ring", 0.82, 0.026, THEME.target, segments=48),
                THEME.target,
                specular=(0.45, 0.75, 0.55, 1.0),
                shininess=42.0,
            )
            ring.reparentTo(marker)
            ring.setZ(0.07)

            beacon = apply_material(
                make_box("target-beacon", (0.22, 0.22, 0.82), THEME.target),
                THEME.target,
                specular=(0.45, 0.95, 0.60, 1.0),
                shininess=48.0,
            )
            beacon.reparentTo(marker)
            beacon.setPos(0, 0, 0.10)

            core = apply_material(
                make_cylinder("target-core", 0.18, 0.16, THEME.target_core, segments=24),
                THEME.target_core,
                specular=(0.60, 1.0, 0.75, 1.0),
                shininess=60.0,
            )
            core.reparentTo(marker)
            core.setPos(0, 0, 0.96)

            marker.setPos(target.x, target.y, 0)
            self.target_nodes.append(marker)
            self.target_visuals.append({"root": marker, "ring": ring, "beacon": beacon, "core": core})

    def _build_rover(self) -> None:
        self.rover.removeNode()
        self.rover = self.render.attachNewNode("rover")
        self.rover_colored_nodes = []
        self.wheel_nodes = []

        parts: tuple[tuple[str, tuple[float, float, float], Color, tuple[float, float, float]], ...] = (
            ("rover-chassis", (1.02, 1.22, 0.20), THEME.rover_dark, (0, 0, 0.12)),
            ("rover-body", (0.82, 0.98, 0.30), THEME.rover_body, (0, 0, 0.24)),
            ("rover-top-panel", (0.56, 0.66, 0.08), THEME.rover_panel, (0, 0, 0.52)),
            ("rover-nose", (0.34, 0.28, 0.20), THEME.rover_accent, (0, 0.62, 0.30)),
            ("sensor-mast", (0.12, 0.12, 0.70), THEME.rover_light, (0, 0.02, 0.56)),
            ("scanner-head", (0.58, 0.15, 0.12), THEME.sensor_glow, (0, 0.05, 1.12)),
        )
        for name, size, color, position in parts:
            node = apply_material(make_box(name, size, color), color, shininess=34.0)
            node.reparentTo(self.rover)
            node.setPos(*position)
            self.rover_colored_nodes.append((node, color))

        for x in (-0.58, 0.58):
            for y in (-0.42, 0.42):
                wheel = apply_material(
                    make_cylinder("wheel", 0.20, 0.16, THEME.rover_dark, segments=24),
                    THEME.rover_dark,
                    shininess=16.0,
                )
                wheel.reparentTo(self.rover)
                wheel.setPos(x, y, 0.18)
                wheel.setP(90)
                self.wheel_nodes.append(wheel)

        for x in (-0.23, 0.23):
            headlight = apply_material(
                make_box("headlight", (0.13, 0.05, 0.07), THEME.rover_light),
                THEME.rover_light,
                specular=(0.9, 0.95, 1.0, 1.0),
                shininess=70.0,
            )
            headlight.reparentTo(self.rover)
            headlight.setPos(x, 0.77, 0.30)

            tail_light = apply_material(
                make_box("tail-light", (0.12, 0.05, 0.06), (0.90, 0.10, 0.08, 1.0)),
                (0.90, 0.10, 0.08, 1.0),
                shininess=42.0,
            )
            tail_light.reparentTo(self.rover)
            tail_light.setPos(x, -0.68, 0.25)

    def _build_hud(self) -> None:
        self.hud = ArenaHud(
            HudCallbacks(
                toggle_autopilot=self._toggle_autopilot,
                toggle_pause=self._toggle_pause,
                step_once=self._single_step,
                toggle_camera=self._toggle_camera_mode,
                toggle_debug=self._toggle_debug,
                reset=self._reset,
                toggle_guide=self._toggle_guide,
                toggle_sensors=lambda: self._toggle_debug_layer("sensors"),
                toggle_bounds=lambda: self._toggle_debug_layer("collision_bounds"),
                toggle_path=lambda: self._toggle_debug_layer("pathfinding"),
                toggle_events=lambda: self._toggle_debug_layer("reward_events"),
            )
        )

    def _bind_controls(self) -> None:
        for key, name in (("w", "forward"), ("s", "reverse"), ("a", "left"), ("d", "right")):
            self.accept(key, self._set_key, [name, True])
            self.accept(f"{key}-up", self._set_key, [name, False])
        self.accept("tab", self._toggle_autopilot)
        self.accept("h", self._toggle_guide)
        self.accept("enter", self._hide_guide)
        self.accept("p", self._toggle_pause)
        self.accept("n", self._single_step)
        self.accept("c", self._toggle_camera_mode)
        self.accept("space", self._reset)
        self.accept("f1", self._toggle_debug)
        self.accept("f2", self._toggle_debug_layer, ["sensors"])
        self.accept("f3", self._toggle_debug_layer, ["collision_bounds"])
        self.accept("f4", self._toggle_debug_layer, ["pathfinding"])
        self.accept("f5", self._toggle_debug_layer, ["reward_events"])
        self.accept("escape", self.userExit)

    def _set_key(self, name: str, value: bool) -> None:
        self.keys[name] = value

    def _toggle_autopilot(self) -> None:
        self.autopilot = not self.autopilot

    def _toggle_guide(self) -> None:
        if self.guide_visible:
            self._hide_guide()
            return
        self.guide_visible = True
        self.guide_pause = True
        self.paused = True

    def _hide_guide(self) -> None:
        self.guide_visible = False
        if self.guide_pause:
            self.paused = False
            self.guide_pause = False
            self._reset_visual_interpolation()

    def _toggle_pause(self) -> None:
        self.paused = not self.paused
        self._reset_visual_interpolation()

    def _single_step(self) -> None:
        self.paused = True
        self.step_once = True

    def _toggle_camera_mode(self) -> None:
        self.camera_mode = "overhead" if self.camera_mode == "chase" else "chase"

    def _toggle_debug(self) -> None:
        enabled = not self.debug.all_enabled()
        self.debug = DebugSettings(
            sensors=enabled,
            collision_bounds=enabled,
            reward_events=enabled,
            pathfinding=enabled,
        )

    def _toggle_debug_layer(self, name: str) -> None:
        current = getattr(self.debug, name)
        setattr(self.debug, name, not current)

    def _reset(self, clear_reward_feed: bool = True) -> None:
        self.seed += 1
        self.env.reset(self.seed)
        self.agent = make_agent(self.agent_name, self.env, seed=self.seed)
        self.last_observation = self.env.observe()
        if clear_reward_feed:
            self.reward_feed = []
            self.episode_summary = ""
            self.episode_summary_ttl = 0.0
        self.reward_markers = []
        self.accumulator = 0.0
        self.step_once = False
        self.camera_ready = False
        self._reset_visual_interpolation()
        self._build_level()

    def _manual_action(self) -> ActionCommand:
        turn = float(self.keys["right"]) - float(self.keys["left"])
        throttle = float(self.keys["forward"]) - float(self.keys["reverse"])
        return {"turn": turn, "throttle": throttle}

    def _agent_pose(self) -> AgentPose:
        return (
            self.env.agent.x,
            self.env.agent.y,
            self.env.agent.heading,
            self.env.agent.speed,
        )

    def _reset_visual_interpolation(self) -> None:
        self.previous_agent_pose = self._agent_pose()
        self.current_agent_pose = self.previous_agent_pose
        self.visual_agent_pose = self.current_agent_pose

    def _update(self, task: Task) -> int:
        dt = ClockObject.getGlobalClock().getDt()
        self.frame_dt = dt
        self.visual_time += dt
        self._age_reward_markers(dt)
        self._age_episode_summary(dt)
        self._age_collision_flash(dt)
        self.accumulator = min(self.accumulator + dt, 0.25)
        if self.paused and not self.step_once:
            self.accumulator = 0.0
            self._sync_visuals()
            return task.cont

        step_budget = self.env.config.step_seconds if self.step_once else self.accumulator
        while step_budget >= self.env.config.step_seconds:
            action = self.agent.act(self.last_observation) if self.autopilot else self._manual_action()
            self.previous_agent_pose = self.current_agent_pose
            result = self.env.step(action)
            self.current_agent_pose = self._agent_pose()
            self.last_observation = result.observation
            self._record_reward_events(result.reward_events)
            if result.done:
                self._record_episode_summary()
                self._reset(clear_reward_feed=False)
            step_budget -= self.env.config.step_seconds
            if self.step_once:
                self.step_once = False
                self.accumulator = 0.0
                break

        if not self.paused:
            self.accumulator = step_budget

        self._sync_visuals()
        return task.cont

    def _sync_visuals(self) -> None:
        self.visual_agent_pose = self._interpolated_agent_pose()
        x, y, heading, _speed = self.visual_agent_pose
        self.rover.setPos(x, y, 0)
        self.rover.setH(math.degrees(-heading))
        self._sync_rover_visuals()

        for index, (visual, target) in enumerate(zip(self.target_visuals, self.env.targets)):
            self._sync_target_visual(index, visual, target.collected)

        self._update_debug_views()
        self._update_camera()
        self._update_overlay()

    def _interpolated_agent_pose(self) -> AgentPose:
        if self.paused:
            return self.current_agent_pose

        alpha = min(
            1.0,
            max(0.0, self.accumulator / self.env.config.step_seconds),
        )
        previous_x, previous_y, previous_heading, previous_speed = self.previous_agent_pose
        current_x, current_y, current_heading, current_speed = self.current_agent_pose
        heading_delta = math.atan2(
            math.sin(current_heading - previous_heading),
            math.cos(current_heading - previous_heading),
        )
        return (
            previous_x + (current_x - previous_x) * alpha,
            previous_y + (current_y - previous_y) * alpha,
            previous_heading + heading_delta * alpha,
            previous_speed + (current_speed - previous_speed) * alpha,
        )

    def _update_camera(self) -> None:
        if self.camera_mode == "overhead":
            cfg = self.env.config
            desired_pos = Vec3(
                0,
                -0.01,
                max(cfg.width, cfg.depth) * self.camera_settings.overhead_height_scale,
            )
            self._set_camera_position(desired_pos)
            self.camera.lookAt(Vec3(0, 0, 0))
            return

        x, y, heading, _speed = self.visual_agent_pose
        back_x = math.sin(heading) * self.camera_settings.chase_distance
        back_y = math.cos(heading) * self.camera_settings.chase_distance
        desired_pos = Vec3(
            x - back_x,
            y - back_y - self.camera_settings.chase_offset,
            self.camera_settings.chase_height,
        )
        self._set_camera_position(desired_pos)
        self.camera.lookAt(Vec3(x, y, self.camera_settings.look_at_height))

    def _set_camera_position(self, desired_pos: Vec3) -> None:
        if not self.camera_ready:
            self.camera.setPos(desired_pos)
            self.camera_ready = True
            return

        blend = 1.0 - math.exp(-self.camera_settings.smoothing * self.frame_dt)
        current = self.camera.getPos()
        self.camera.setPos(current + (desired_pos - current) * blend)

    def _sync_target_visual(
        self,
        index: int,
        visual: dict[str, NodePath],
        collected: bool,
    ) -> None:
        root = visual["root"]
        if collected:
            root.hide()
            return

        root.show()
        phase = self.visual_time * self.visual_settings.target_bob_speed + index * 0.7
        bob = math.sin(phase) * self.visual_settings.target_bob_height
        root.setZ(bob)

        ring = visual["ring"]
        ring.setH(self.visual_time * self.visual_settings.target_spin_speed + index * 22.0)

        core = visual["core"]
        pulse = 1.0 + math.sin(phase * 1.7) * 0.12
        core.setScale(pulse)

    def _sync_rover_visuals(self) -> None:
        speed = self.visual_agent_pose[3]
        self.wheel_rotation += speed * self.visual_settings.wheel_spin_scale * self.frame_dt
        for wheel in self.wheel_nodes:
            wheel.setH(self.wheel_rotation)

        if self.collision_flash_timer > 0.0:
            for node, _color in self.rover_colored_nodes:
                node.setColor(*THEME.collision_flash)
            return

        for node, color in self.rover_colored_nodes:
            node.setColor(*color)

    def _update_debug_views(self) -> None:
        self._update_sensor_lines()
        self._update_collision_bounds()
        self._update_pathfinding()
        self._update_reward_markers()

    def _update_sensor_lines(self) -> None:
        if self.sensor_node is not None:
            self.sensor_node.removeNode()
            self.sensor_node = None

        if not self.debug.sensors:
            return

        self.sensor_node = self.render.attachNewNode(self._build_sensor_lines(self.last_observation))

    def _build_sensor_lines(self, observation: Observation) -> PandaNode:
        lines = LineSegs("sensor-rays")
        lines.setThickness(2.0)
        x, y, heading, _speed = self.visual_agent_pose
        z = 0.72

        for angle_degrees, normalized in zip(observation["sensor_angles"], observation["sensors"]):
            distance = normalized * observation["sensor_range"]
            angle = heading + math.radians(angle_degrees)
            end_x = x + math.sin(angle) * distance
            end_y = y + math.cos(angle) * distance

            if normalized < 0.30:
                lines.setColor(0.96, 0.24, 0.22, 1.0)
            else:
                lines.setColor(0.18, 0.88, 0.62, 1.0)
            lines.moveTo(x, y, z)
            lines.drawTo(end_x, end_y, z)

        return lines.create()

    def _update_collision_bounds(self) -> None:
        if self.bounds_node is not None:
            self.bounds_node.removeNode()
            self.bounds_node = None

        if not self.debug.collision_bounds:
            return

        self.bounds_node = self.render.attachNewNode("collision-bounds")
        cfg = self.env.config
        agent_x, agent_y, _heading, _speed = self.visual_agent_pose
        self.bounds_node.attachNewNode(circle_outline(
            "agent-radius",
            agent_x,
            agent_y,
            cfg.agent_radius,
            0.08,
            (0.30, 0.70, 1.0, 1.0),
        ))

        for obstacle in self.env.obstacles:
            self.bounds_node.attachNewNode(rectangle_outline(
                "obstacle-bounds",
                obstacle.min_x,
                obstacle.max_x,
                obstacle.min_y,
                obstacle.max_y,
                0.09,
                (1.0, 0.42, 0.18, 1.0),
            ))

        for target in self.env.active_targets():
            self.bounds_node.attachNewNode(circle_outline(
                "target-radius",
                target.x,
                target.y,
                cfg.target_radius,
                0.10,
                (0.16, 0.95, 0.52, 1.0),
                segments=28,
            ))

    def _update_pathfinding(self) -> None:
        if self.path_node is not None:
            self.path_node.removeNode()
            self.path_node = None

        if not self.debug.pathfinding:
            return

        path = getattr(self.agent, "path", ())
        if not self.autopilot or not isinstance(self.agent, GridPlannerAgent) or not path:
            return

        agent_x, agent_y, _heading, _speed = self.visual_agent_pose
        points = [(agent_x, agent_y), *path]
        self.path_node = self.render.attachNewNode(
            polyline("planner-path", points, 0.18, (0.95, 0.82, 0.22, 1.0), thickness=4.0)
        )

    def _record_reward_events(self, events: list[RewardEvent]) -> None:
        for event in events:
            if event.value == 0.0:
                continue
            if event.label == "collision":
                self.collision_flash_timer = self.visual_settings.collision_flash_seconds
            sign = "+" if event.value > 0.0 else ""
            self.reward_feed.insert(0, f"{event.step}: {event.label} {sign}{event.value:.2f}")
            self.reward_markers.append(RewardMarkerState(event))
        self.reward_feed = self.reward_feed[:4]

    def _age_reward_markers(self, dt: float) -> None:
        for marker in self.reward_markers:
            marker.ttl -= dt
        self.reward_markers = [marker for marker in self.reward_markers if marker.ttl > 0.0]

    def _age_collision_flash(self, dt: float) -> None:
        self.collision_flash_timer = max(0.0, self.collision_flash_timer - dt)

    def _record_episode_summary(self) -> None:
        self.episode_summary = (
            f"last episode: {self.env.terminal_reason} | "
            f"steps {self.env.steps} | reward {self.env.total_reward:.2f}"
        )
        self.episode_summary_ttl = 4.0

    def _age_episode_summary(self, dt: float) -> None:
        if self.episode_summary_ttl <= 0.0:
            self.episode_summary = ""
            return
        self.episode_summary_ttl -= dt

    def _update_reward_markers(self) -> None:
        if self.reward_node is not None:
            self.reward_node.removeNode()
            self.reward_node = None

        if not self.debug.reward_events or not self.reward_markers:
            return

        self.reward_node = self.render.attachNewNode("reward-markers")
        for marker in self.reward_markers:
            x, y = marker.event.position
            self.reward_node.attachNewNode(
                make_reward_marker("reward-marker", x, y, marker.event.value)
            )

    def _update_overlay(self) -> None:
        obs = self.last_observation
        mode = "guide" if self.guide_visible else (
            "paused" if self.paused else ("autopilot" if self.autopilot else "manual")
        )
        self.hud.update(
            obs,
            mode=mode,
            agent_name=self.agent_name,
            seed=self.env.seed,
            target_count=len(self.env.targets),
            max_steps=self.env.config.max_steps,
            camera_mode=self.camera_mode,
            total_reward=self.env.total_reward,
            native_status=native_status(),
            reward_feed=self.reward_feed,
            show_reward_feed=self.debug.reward_events,
            debug_layers={
                "sensors": self.debug.sensors,
                "bounds": self.debug.collision_bounds,
                "path": self.debug.pathfinding,
                "events": self.debug.reward_events,
            },
            autopilot=self.autopilot,
            paused=self.paused,
            guide_visible=self.guide_visible,
            episode_summary=self.episode_summary,
        )
