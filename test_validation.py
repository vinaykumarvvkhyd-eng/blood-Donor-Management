import unittest
from bloodcare.validation import validate_donor, validate_age, validate_phone, validate_blood_group

GOOD = {"name":"Aditi Sharma","age":"24","gender":"Female","phone":"9876543210",
        "blood_group":"O+","city":"Hyderabad","camp_date":"2026-12-15","status":"Registered"}

class ValidationTests(unittest.TestCase):
    def test_valid_record(self):
        result=validate_donor(GOOD)
        self.assertEqual(result["blood_group"],"O+")
        self.assertEqual(result["age"],24)
    def test_age_boundaries(self):
        self.assertEqual(validate_age("18"),18)
        self.assertEqual(validate_age("65"),65)
        for value in ("17","66","abc",""):
            with self.subTest(value=value), self.assertRaises(ValueError): validate_age(value)
    def test_phone(self):
        self.assertEqual(validate_phone("9876543210"),"9876543210")
        for value in ("1234567890","98765","abcdefghij"):
            with self.subTest(value=value), self.assertRaises(ValueError): validate_phone(value)
    def test_blood_group(self):
        self.assertEqual(validate_blood_group("ab+"),"AB+")
        with self.assertRaises(ValueError): validate_blood_group("X+")
    def test_invalid_name_and_date(self):
        for patch in ({"name":"A"},{"name":"<script>"},{"camp_date":"15-12-2026"}):
            data={**GOOD,**patch}
            with self.subTest(patch=patch), self.assertRaises(ValueError): validate_donor(data)

if __name__=="__main__": unittest.main()
