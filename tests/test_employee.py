import pytest


class TestNormalisePhotoValue:
    """The CSV photo column shows up in many shapes in the wild. The
    helper collapses every one of them to the canonical
    `/photos/<filename>` form so the route + templates work uniformly."""

    @pytest.mark.parametrize('raw, expected', [
        # Already canonical — idempotent.
        ('/photos/alice.jpg', '/photos/alice.jpg'),
        # Bare filename.
        ('alice.jpg', '/photos/alice.jpg'),
        # User-export style with output/photos prefix (the Infolegale case).
        ('output/photos/alice.jpg', '/photos/alice.jpg'),
        # Relative dot-slash.
        ('./photos/alice.jpg', '/photos/alice.jpg'),
        # Windows backslashes.
        ('output\\photos\\alice.jpg', '/photos/alice.jpg'),
        # Drive-letter absolute.
        ('C:/photos/alice.jpg', '/photos/alice.jpg'),
        # Surrounding whitespace.
        ('  alice.jpg  ', '/photos/alice.jpg'),
    ])
    def test_normalises_to_canonical(self, raw, expected):
        from models.employee import normalise_photo_value
        assert normalise_photo_value(raw) == expected

    @pytest.mark.parametrize('raw', ['', None, '   ', '/'])
    def test_empty_and_pathological_returns_blank(self, raw):
        from models.employee import normalise_photo_value
        assert normalise_photo_value(raw) == ''

    def test_nan_returns_blank(self):
        # pandas hands `float('nan')` for empty CSV cells.
        from models.employee import normalise_photo_value
        assert normalise_photo_value(float('nan')) == ''

    @pytest.mark.parametrize('raw, expected', [
        # The two cases the user reported on the Infolegale dataset.
        ('output/photos/197_Laurène_ANGELIN--BONNET.jpg',
         '/photos/197_Laurene_ANGELIN--BONNET.jpg'),
        ('/photos/132_Loïc_ARBAN.jpg',
         '/photos/132_Loic_ARBAN.jpg'),
        # Other common French / Spanish / German diacritics.
        ('Léa.jpg', '/photos/Lea.jpg'),
        ('François.png', '/photos/Francois.png'),
        ('Müller.jpg', '/photos/Muller.jpg'),
        # Spaces collapse to underscores.
        ('Marie  Curie.jpg', '/photos/Marie_Curie.jpg'),
    ])
    def test_accents_match_secure_filename_output(self, raw, expected):
        # The on-disk filename produced by werkzeug.secure_filename at
        # ZIP extraction time must equal what we store on the CSV side
        # — otherwise the « photo missing » check fires falsely.
        from models.employee import normalise_photo_value
        assert normalise_photo_value(raw) == expected


class TestEmployeeData:
    def test_load_employees(self, test_employee_data):
        employees = test_employee_data.get_all_employees()
        assert len(employees) == 10

    def test_canonical_field_names(self, test_employee_data):
        employees = test_employee_data.get_all_employees()
        first = employees[0]
        assert 'first_name' in first
        assert 'last_name' in first
        assert 'photo' in first
        assert 'team' in first
        assert 'job_title' in first
        assert 'company' in first
        assert 'sex' in first

    def test_original_columns_renamed(self, test_employee_data):
        employees = test_employee_data.get_all_employees()
        first = employees[0]
        assert 'firstName' not in first
        assert 'lastName' not in first
        assert 'image_path' not in first

    def test_get_random_employees_count(self, test_employee_data):
        result = test_employee_data.get_random_employees(3)
        assert len(result) == 3

    def test_get_random_employees_single(self, test_employee_data):
        result = test_employee_data.get_random_employees(1)
        assert len(result) == 1
        assert 'first_name' in result[0]

    def test_get_filtered_employees_by_sex(self, test_employee_data):
        men = test_employee_data.get_filtered_employees({'sex': 'man'})
        assert all(e['sex'] == 'man' for e in men)
        assert len(men) == 5

    def test_get_filtered_employees_by_company(self, test_employee_data):
        corp = test_employee_data.get_filtered_employees({'company': 'TestCorp'})
        assert all(e['company'] == 'TestCorp' for e in corp)
        assert len(corp) == 6

    def test_get_filtered_employees_multiple_filters(self, test_employee_data):
        result = test_employee_data.get_filtered_employees({'sex': 'woman', 'company': 'PartnerInc'})
        assert len(result) == 2
        assert all(e['sex'] == 'woman' and e['company'] == 'PartnerInc' for e in result)

    def test_get_unique_values_company(self, test_employee_data):
        companies = test_employee_data.get_unique_values('company')
        assert set(companies) == {'TestCorp', 'PartnerInc'}

    def test_get_unique_values_sex(self, test_employee_data):
        sexes = test_employee_data.get_unique_values('sex')
        assert set(sexes) == {'man', 'woman'}

    def test_get_random_choices_count(self, test_employee_data):
        choices = test_employee_data.get_random_choices('team', 'Engineering', count=4)
        assert len(choices) == 4

    def test_get_random_choices_includes_correct(self, test_employee_data):
        choices = test_employee_data.get_random_choices('team', 'Engineering', count=4)
        assert 'Engineering' in choices

    def test_get_random_choices_with_filter(self, test_employee_data):
        choices = test_employee_data.get_random_choices(
            'job_title', 'Software Engineer', count=3, filter_dict={'sex': 'woman'}
        )
        assert 'Software Engineer' in choices
        assert len(choices) <= 3

    def test_get_random_choices_few_unique_values(self, test_employee_data):
        choices = test_employee_data.get_random_choices('company', 'TestCorp', count=10)
        assert 'TestCorp' in choices
        assert len(choices) == 2  # only 2 unique companies

    def test_get_random_choices_falls_back_when_filter_too_narrow(
        self, test_employee_data
    ):
        """Regression: Infolegale dataset mapped `sex` to a unique-per-row
        column (`id`), so the filter `{sex: <one row's id>}` returned a
        single match and the question only got one choice. The robustness
        guard now falls back to the unfiltered pool when the filter
        narrows below `count`."""
        first = test_employee_data.get_all_employees()[0]
        # sex='nonsense' won't match any row → filtered pool is empty.
        choices = test_employee_data.get_random_choices(
            'job_title', first['job_title'], count=4,
            filter_dict={'sex': '__no_match__'},
        )
        # We still get 4 distinct values from the unfiltered pool,
        # the correct one included.
        assert first['job_title'] in choices
        assert len(choices) == 4
        assert len(set(choices)) == 4

    @pytest.mark.parametrize('count', [1, 2, 4])
    def test_get_random_employees_parametrized(self, test_employee_data, count):
        result = test_employee_data.get_random_employees(count)
        assert len(result) == count


class TestEmployeeCrud:
    """CRUD mutations on EmployeeData write back to CSV with CSV column names."""

    def _build(self, tmp_path):
        from models.config import DatasetConfig
        from models.employee import EmployeeData

        csv = tmp_path / 'team.csv'
        csv.write_text(
            'firstName,lastName,photo_path,team,jobTitle,company,sex\n'
            'Alice,Dupont,alice.jpg,Eng,Dev,Acme,F\n'
            'Bob,Martin,bob.jpg,Sales,Rep,Acme,M\n'
        )
        config = DatasetConfig(
            'acme',
            {
                'data': {
                    'csv_path': str(csv),
                    'column_mapping': {
                        'first_name': 'firstName', 'last_name': 'lastName',
                        'photo': 'photo_path', 'team': 'team',
                        'job_title': 'jobTitle', 'company': 'company', 'sex': 'sex',
                    },
                },
            },
        )
        return csv, EmployeeData(config)

    def test_get_by_index(self, tmp_path):
        _, ed = self._build(tmp_path)
        emp = ed.get_by_index(0)
        assert emp['first_name'] == 'Alice'
        assert emp['last_name'] == 'Dupont'

    def test_get_by_index_out_of_range(self, tmp_path):
        _, ed = self._build(tmp_path)
        with pytest.raises(IndexError):
            ed.get_by_index(99)

    def test_update_persists_with_original_column_names(self, tmp_path):
        csv, ed = self._build(tmp_path)
        ed.update_at_index(0, {'first_name': 'Alicia', 'team': 'Platform'})
        ed.save()

        # Reload from disk and verify CSV column names are restored.
        # Photo column is normalised at load time so the bare `alice.jpg`
        # roundtrips back as `/photos/alice.jpg`.
        reloaded = csv.read_text()
        assert 'Alicia,Dupont,/photos/alice.jpg,Platform' in reloaded
        # Header uses CSV column names, not canonical
        assert reloaded.splitlines()[0] == 'firstName,lastName,photo_path,team,jobTitle,company,sex'

    def test_append_and_save(self, tmp_path):
        csv, ed = self._build(tmp_path)
        idx = ed.append({
            'first_name': 'Carole', 'last_name': 'Zoe', 'photo': 'carole.jpg',
            'team': 'HR', 'job_title': 'Lead', 'company': 'Acme', 'sex': 'F',
        })
        assert idx == 2
        ed.save()
        # `append` normalises the photo write so the bare filename
        # ends up canonical on disk.
        assert 'Carole,Zoe,/photos/carole.jpg' in csv.read_text()

    def test_delete_and_save(self, tmp_path):
        csv, ed = self._build(tmp_path)
        ed.delete_at_index(0)
        ed.save()
        content = csv.read_text()
        assert 'Alice' not in content
        assert 'Bob' in content

    def test_save_does_not_leak_canonical_column_names(self, tmp_path):
        csv, ed = self._build(tmp_path)
        ed.update_at_index(0, {'first_name': 'Alicia'})
        ed.save()
        content = csv.read_text()
        # Canonical names should not appear as CSV headers
        assert 'first_name' not in content.splitlines()[0]
        assert 'job_title' not in content.splitlines()[0]
