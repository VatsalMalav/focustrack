import argparse
import signal
import time
from datetime import datetime

from alarm import AlarmManager
from attention import AttentionState
from capture import capture_snapshot, save_labeled_snapshot
from config import DISTRACTED_THRESHOLD_SEC, SNAPSHOT_INTERVAL_SEC, SNAPSHOTS_DIR
from pose import HeadPoseEstimator


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _format_pose(pose) -> str:
    if pose is None:
        return "no face"
    return f"yaw={pose.yaw:+.1f} pitch={pose.pitch:+.1f} roll={pose.roll:+.1f}"


def _snapshot_status(attention: AttentionState, pose) -> str:
    if pose is None:
        return "NO_FACE"
    if attention.is_focused:
        return "FOCUSED"
    return "DISTRACTED"


def run(calibrate: bool = False) -> None:
    print("FocusTrack starting...")
    print("Safe zone: yaw [-20, +20], pitch [-30, +20] (screen + desk/keyboard)")
    print(
        f"Snapshot every {SNAPSHOT_INTERVAL_SEC}s | "
        f"alarm after {DISTRACTED_THRESHOLD_SEC}s distracted | "
        "alarm.wav loops until focused or app closed"
    )
    print(f"Labeled snapshots saved to: {SNAPSHOTS_DIR}")
    print("Press Ctrl+C to stop.\n")

    estimator = HeadPoseEstimator()
    attention = AttentionState()
    alarm = AlarmManager()
    running = True

    def handle_exit(signum, frame) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, handle_exit)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, handle_exit)

    try:
        while running:
            loop_start = time.time()
            frame = capture_snapshot()

            if frame is None:
                print(f"[{_timestamp()}] Camera error - could not capture frame.")
                attention.update(None)
            else:
                pose = estimator.estimate(frame)
                attention.update(pose)
                status = _snapshot_status(attention, pose)

                saved_path = save_labeled_snapshot(
                    frame,
                    status=status,
                    pose=pose,
                    distracted_seconds=attention.distracted_seconds,
                    alarm_active=alarm.is_active,
                )

                if calibrate:
                    print(f"[{_timestamp()}] {status} | {_format_pose(pose)} | saved {saved_path}")
                elif attention.is_focused:
                    print(f"[{_timestamp()}] Focused | {_format_pose(pose)} | saved")
                else:
                    print(
                        f"[{_timestamp()}] Distracted ({attention.distracted_seconds:.0f}s) "
                        f"| {_format_pose(pose)} | saved"
                    )

            if attention.is_focused:
                if alarm.is_active:
                    print(f"[{_timestamp()}] Focused - stopping alarm.")
                alarm.stop()
            elif attention.should_ring():
                if not alarm.is_active:
                    print(f"[{_timestamp()}] ALARM STARTED (playing alarm.wav)")
                alarm.start()

            elapsed = time.time() - loop_start
            sleep_for = max(0.0, SNAPSHOT_INTERVAL_SEC - elapsed)
            time.sleep(sleep_for)
    finally:
        alarm.stop()
        estimator.close()
        print("\nFocusTrack stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="FocusTrack distraction monitor")
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Print yaw/pitch/roll every snapshot to tune safe-zone angles.",
    )
    parser.add_argument(
        "--test-alarm",
        action="store_true",
        help="Ring the alarm for 5 seconds and exit (sound check).",
    )
    args = parser.parse_args()
    if args.test_alarm:
        alarm = AlarmManager()
        print("Testing alarm for 5 seconds...")
        alarm.start()
        time.sleep(5)
        alarm.stop()
        print("Alarm test done.")
        return
    run(calibrate=args.calibrate)


if __name__ == "__main__":
    main()
