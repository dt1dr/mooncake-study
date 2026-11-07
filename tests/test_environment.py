import pytest

from env.check_env import PACKAGES, check_track


def baseline():
    return {
        "python": "3.13.17",
        "platform": "Linux",
        "machine": "x86_64",
        "libc": ["glibc", "2.39"],
        "packages": dict.fromkeys(PACKAGES),
    }


def test_cpu_needs_no_gpu_or_mooncake():
    assert check_track(baseline(), "portable-cpu") == []


@pytest.mark.parametrize("system", ["Windows", "Darwin"])
def test_store_rejects_unsupported_platform(system):
    report = baseline()
    report["platform"] = system
    report["packages"]["mooncake-transfer-engine-non-cuda"] = "0.3.13.post1"
    assert check_track(report, "linux-cpu")


@pytest.mark.parametrize("libc", [["glibc", "2.28"], ["musl", "1.2.5"], ["", ""]])
def test_project_store_baseline(libc):
    report = baseline()
    report["libc"] = libc
    report["packages"]["mooncake-transfer-engine-non-cuda"] = "0.3.13.post1"
    assert check_track(report, "linux-cpu")


def test_conflicting_wheel_flavors_fail():
    report = baseline()
    report["packages"]["mooncake-transfer-engine-non-cuda"] = "0.3.13.post1"
    report["packages"]["mooncake-transfer-engine-cuda13"] = "0.3.13.post1"
    assert check_track(report, "linux-cpu")
