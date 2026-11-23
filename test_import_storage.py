import csv, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from bloodcare import storage, services

class ImportAndRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.patches = [
            patch('bloodcare.storage.DATA_DIR', self.base),
            patch('bloodcare.storage.DONORS_JSON', self.base / 'donors.json'),
            patch('bloodcare.storage.DONORS_CSV', self.base / 'donors.csv'),
            patch('bloodcare.storage.AUDIT_LOG', self.base / 'audit.log'),
        ]
        for item in self.patches: item.start()
        storage.ensure_storage()

    def tearDown(self):
        for item in reversed(self.patches): item.stop()
        self.temp.cleanup()

    def test_corrupt_json_is_backed_up_and_recovered(self):
        (self.base / 'donors.json').write_text('{broken json', encoding='utf-8')
        self.assertEqual(storage.load_records(), [])
        self.assertTrue((self.base / 'donors.corrupt.json').exists())
        self.assertEqual((self.base / 'donors.json').read_text(encoding='utf-8').strip(), '[]')

    def test_bulk_import_reports_bad_rows(self):
        source = self.base / 'legacy.csv'
        with source.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=['name','age','gender','phone','blood_group','city','camp_date','status'])
            writer.writeheader()
            writer.writerow({'name':'Aditi Sharma','age':'24','gender':'Female','phone':'9876543210','blood_group':'O+','city':'Hyderabad','camp_date':'2026-12-15','status':'Registered'})
            writer.writerow({'name':'Bad Entry','age':'12','gender':'Male','phone':'9876543211','blood_group':'X+','city':'Hyderabad','camp_date':'bad-date','status':'Registered'})
        result = services.import_csv(source)
        self.assertEqual(result['imported'], 1)
        self.assertEqual(len(result['errors']), 1)
        self.assertEqual(result['errors'][0]['row'], 3)

if __name__ == '__main__': unittest.main()
