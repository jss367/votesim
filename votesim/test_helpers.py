from typing import Any, List


def almost_equal(value1: float, value2: float, considered_equal_margin: float = 0.001) -> bool:
    return abs(value1 - value2) < considered_equal_margin


def assert_list_almost_equal(test_obj: Any, correct_list: List, li: List, considered_equal_margin=0.0001, msg=""):
    """
    Assert that two lists are almost equal (within a margin of error).

    Args:
        test_obj: Object that provides assertion methods assertEqual and assertTrue
        correct_list: Expected list of values
        li: Actual list of values to compare
        considered_equal_margin: Maximum allowed difference between values
        msg: Optional message to display on failure
    """
    test_obj.assertEqual(len(correct_list), len(li), "List should be of same length")

    almost_equal_entries = [
        almost_equal(correct_list[i], li[i], considered_equal_margin) for i in range(len(correct_list))
    ]

    if not msg:
        msg = f"{li} should have been almost equal to {correct_list}"
    test_obj.assertTrue(all(almost_equal_entries), msg)
