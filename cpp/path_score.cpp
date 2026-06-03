#include <algorithm>
#include <cmath>

#if defined(_WIN32)
#if defined(ARENA_NATIVE_EXPORTS)
#define ARENA_API __declspec(dllexport)
#else
#define ARENA_API __declspec(dllimport)
#endif
#else
#define ARENA_API
#endif

extern "C" {

ARENA_API double score_path(const double* sensors, int count, double target_dx, double target_dy) {
    if (sensors == nullptr || count <= 0) {
        return 0.0;
    }

    double clearance_sum = 0.0;
    for (int index = 0; index < count; ++index) {
        clearance_sum += std::clamp(sensors[index], 0.0, 1.0);
    }

    const int center = count / 2;
    const int start = std::max(0, center - 1);
    const int end = std::min(count, center + 2);
    double front_sum = 0.0;
    for (int index = start; index < end; ++index) {
        front_sum += std::clamp(sensors[index], 0.0, 1.0);
    }

    const double average_clearance = clearance_sum / static_cast<double>(count);
    const double front_clearance = front_sum / static_cast<double>(end - start);
    const double target_distance = std::max(std::hypot(target_dx, target_dy), 0.001);
    const double forward_alignment = target_dy / target_distance;

    return 0.55 * front_clearance + 0.25 * average_clearance + 0.20 * forward_alignment;
}

}
