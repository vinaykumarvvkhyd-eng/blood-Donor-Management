import unittest, tempfile
from pathlib import Path
from unittest.mock import patch
from bloodcare import storage, services

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        base=Path(self.temp.name)
        self.patches=[
            patch("bloodcare.storage.DATA_DIR",base),
            patch("bloodcare.storage.DONORS_JSON",base/"donors.json"),
            patch("bloodcare.storage.DONORS_CSV",base/"donors.csv"),
            patch("bloodcare.storage.AUDIT_LOG",base/"audit.log"),
            patch("bloodcare.services.load_records", side_effect=lambda: storage.load_records()),
            patch("bloodcare.services.save_records", side_effect=lambda r: storage.save_records(r)),
            patch("bloodcare.services.append_audit", side_effect=lambda *a: storage.append_audit(*a)),
        ]
        for p in self.patches:p.start()
        storage.ensure_storage()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def payload(self,phone="9876543210"):
        return {"name":"Aditi Sharma","age":24,"gender":"Female","phone":phone,
                "blood_group":"O+","city":"Hyderabad","camp_date":"2026-12-15","status":"Registered"}
    def test_create_search_summary_and_delete(self):
        donor=services.add_donor(self.payload())
        self.assertEqual(len(services.search_donors("aditi")),1)
        self.assertEqual(services.summary()["total"],1)
        services.delete_donor(donor["id"])
        self.assertEqual(services.summary()["total"],0)
    def test_duplicate_prevention(self):
        services.add_donor(self.payload())
        with self.assertRaises(ValueError):services.add_donor(self.payload())

if __name__=="__main__":unittest.main()
