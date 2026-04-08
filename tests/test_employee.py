import pytest


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

    @pytest.mark.parametrize('count', [1, 2, 4])
    def test_get_random_employees_parametrized(self, test_employee_data, count):
        result = test_employee_data.get_random_employees(count)
        assert len(result) == count
