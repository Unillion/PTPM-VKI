import datetime
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from delivery import calculate_delivery_cost  # noqa: E402

ERROR_RESULT = (-1, "0000-00-00")
SEND_DATE = datetime.date(2026, 9, 3)


def date_after(days: int) -> str:
    return (SEND_DATE + datetime.timedelta(days=days)).strftime("%Y-%m-%d")


def cost(weight, distance, package_type="обычный", express=False) -> int:
    return calculate_delivery_cost(weight, distance, package_type, express)[0]


def delivery_date(weight, distance, package_type="обычный", express=False) -> datetime.date:
    raw = calculate_delivery_cost(weight, distance, package_type, express)[1]
    return datetime.date.fromisoformat(raw)

class TestInputLimits(unittest.TestCase):

    def test_minimum_weight_is_accepted(self):
        self.assertEqual(calculate_delivery_cost(0.1, 100, "обычный")[0], 700)

    def test_weight_below_minimum_is_rejected(self):
        self.assertEqual(calculate_delivery_cost(0.09, 100, "обычный"), ERROR_RESULT)

    def test_zero_weight_is_rejected(self):
        self.assertEqual(calculate_delivery_cost(0, 100, "обычный"), ERROR_RESULT)

    def test_negative_weight_is_rejected(self):
        self.assertEqual(calculate_delivery_cost(-5, 100, "обычный"), ERROR_RESULT)

    def test_maximum_weight_is_accepted(self):
        self.assertNotEqual(calculate_delivery_cost(50.0, 100, "обычный"), ERROR_RESULT)

    def test_weight_above_maximum_is_rejected(self):
        self.assertEqual(calculate_delivery_cost(50.01, 100, "обычный"), ERROR_RESULT)

    def test_minimum_distance_is_accepted(self):
        self.assertEqual(calculate_delivery_cost(1, 1, "обычный"), (205, date_after(1)))

    def test_zero_distance_is_rejected(self):
        self.assertEqual(calculate_delivery_cost(1, 0, "обычный"), ERROR_RESULT)

    def test_negative_distance_is_rejected(self):
        self.assertEqual(calculate_delivery_cost(1, -10, "обычный"), ERROR_RESULT)

    def test_maximum_distance_is_accepted(self):
        self.assertEqual(calculate_delivery_cost(1, 5000, "обычный"), (25200, date_after(10)))

    def test_distance_above_maximum_is_rejected(self):
        self.assertEqual(calculate_delivery_cost(1, 5001, "обычный"), ERROR_RESULT)

class TestInputTypes(unittest.TestCase):

    def test_unknown_package_type_is_rejected(self):
        self.assertEqual(calculate_delivery_cost(1, 100, "срочный"), ERROR_RESULT)

    def test_empty_package_type_is_rejected(self):
        self.assertEqual(calculate_delivery_cost(1, 100, ""), ERROR_RESULT)

    def test_none_package_type_is_rejected(self):
        self.assertEqual(calculate_delivery_cost(1, 100, None), ERROR_RESULT)

    def test_all_valid_package_types_are_accepted(self):
        for package_type in ("обычный", "хрупкий", "опасный"):
            with self.subTest(package_type=package_type):
                self.assertNotEqual(calculate_delivery_cost(1, 100, package_type), ERROR_RESULT)

    def test_nan_weight_is_rejected(self):
        self.assertEqual(calculate_delivery_cost(math.nan, 100, "обычный"), ERROR_RESULT)

    def test_none_weight_returns_error_instead_of_exception(self):
        self.assertEqual(calculate_delivery_cost(None, 100, "обычный"), ERROR_RESULT)

    def test_string_weight_returns_error_instead_of_exception(self):
        self.assertEqual(calculate_delivery_cost("5", 100, "обычный"), ERROR_RESULT)

    def test_none_distance_returns_error_instead_of_exception(self):
        self.assertEqual(calculate_delivery_cost(1, None, "обычный"), ERROR_RESULT)

    def test_fractional_distance_is_rejected(self):
        # по сигнатуре дистанция - целое число километров
        self.assertEqual(calculate_delivery_cost(1, 100.5, "обычный"), ERROR_RESULT)


class TestCost(unittest.TestCase):

    def test_base_cost_for_light_regular_parcel(self):
        self.assertEqual(cost(1, 100), 700)

    def test_cost_grows_by_five_rubles_per_kilometre(self):
        self.assertEqual(cost(1, 200) - cost(1, 100), 500)

    def test_weight_just_below_five_kg_has_no_surcharge(self):
        self.assertEqual(cost(4.99, 100), 700)

    def test_weight_exactly_five_kg_uses_medium_coefficient(self):
        self.assertEqual(cost(5.0, 100), 840)

    def test_weight_just_above_five_kg_uses_medium_coefficient(self):
        self.assertEqual(cost(5.01, 100), 840)

    def test_weight_just_below_twenty_kg_uses_medium_coefficient(self):
        self.assertEqual(cost(19.99, 100), 840)

    def test_weight_exactly_twenty_kg_uses_heavy_coefficient(self):
        self.assertEqual(cost(20.0, 100), 1050)

    def test_maximum_weight_uses_heavy_coefficient(self):
        self.assertEqual(cost(50.0, 100), 1050)

    def test_fragile_parcel_adds_300_rubles(self):
        self.assertEqual(cost(1, 100, "хрупкий"), 1000)

    def test_dangerous_parcel_adds_1000_rubles(self):
        self.assertEqual(cost(1, 100, "опасный"), 1700)

    def test_weight_coefficient_combines_with_type_surcharge(self):
        self.assertEqual(cost(10, 100, "хрупкий"), 700 * 1.2 + 300)

    def test_most_expensive_regular_delivery(self):
        self.assertEqual(cost(50, 5000, "опасный"), 38800)

    def test_cost_is_integer(self):
        self.assertIsInstance(cost(10, 101), int)

class TestDeliveryDate(unittest.TestCase):

    def test_short_distance_takes_one_day(self):
        self.assertEqual(calculate_delivery_cost(1, 499, "обычный")[1], date_after(1))

    def test_distance_of_500_km_takes_one_day(self):
        self.assertEqual(calculate_delivery_cost(1, 500, "обычный")[1], date_after(1))

    def test_distance_of_999_km_takes_one_day(self):
        self.assertEqual(calculate_delivery_cost(1, 999, "обычный")[1], date_after(1))

    def test_distance_of_1000_km_takes_two_days(self):
        self.assertEqual(calculate_delivery_cost(1, 1000, "обычный")[1], date_after(2))

    def test_longest_distance_takes_ten_days(self):
        self.assertEqual(calculate_delivery_cost(1, 5000, "обычный")[1], date_after(10))

    def test_date_has_iso_format(self):
        date_str = calculate_delivery_cost(1, 100, "обычный")[1]
        self.assertRegex(date_str, r"^\d{4}-\d{2}-\d{2}$")

    def test_weight_and_type_do_not_change_delivery_date(self):
        self.assertEqual(
            calculate_delivery_cost(50, 1500, "опасный")[1],
            calculate_delivery_cost(1, 1500, "обычный")[1],
        )

class TestExpress(unittest.TestCase):

    def test_express_is_more_expensive_than_regular(self):
        self.assertGreater(cost(1, 100, express=True), cost(1, 100, express=False))

    def test_express_is_more_expensive_for_fragile_parcel(self):
        self.assertGreater(cost(10, 1000, "хрупкий", True), cost(10, 1000, "хрупкий", False))

    def test_express_is_more_expensive_for_heavy_dangerous_parcel(self):
        self.assertGreater(cost(30, 3000, "опасный", True), cost(30, 3000, "опасный", False))

    def test_express_halves_delivery_time_on_long_distance(self):
        self.assertEqual(calculate_delivery_cost(1, 2000, "обычный", True)[1], date_after(2))

    def test_express_is_faster_than_regular_on_long_distance(self):
        self.assertLess(delivery_date(1, 3000, express=True), delivery_date(1, 3000))

    def test_express_is_not_slower_than_regular_on_short_distance(self):
        self.assertLessEqual(delivery_date(1, 100, express=True), delivery_date(1, 100))

    def test_express_on_short_distance_is_not_delivered_on_send_date(self):
        self.assertGreater(delivery_date(1, 100, express=True), SEND_DATE)

    def test_express_on_distance_below_1000_km_is_not_delivered_on_send_date(self):
        self.assertGreater(delivery_date(1, 999, express=True), SEND_DATE)

    def test_express_still_validates_input(self):
        self.assertEqual(calculate_delivery_cost(51, 100, "обычный", True), ERROR_RESULT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
