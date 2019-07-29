def verify_test_case(  # noqa: E302
    test_case_element,
    expected_attributes,
    error_message=None,
    error_output=None,
    error_type=None,
    failure_message=None,
    failure_output=None,
    failure_type=None,
    skipped_message=None,
    skipped_output=None,
    stdout=None,
    stderr=None,
):
    for k, v in expected_attributes.items():
        assert test_case_element.attributes[k].value == v

    for k in test_case_element.attributes.keys():
        assert k in expected_attributes.keys()

        if stderr:
            assert test_case_element.getElementsByTagName("system-err")[0].firstChild.nodeValue.strip() == stderr
        if stdout:
            assert test_case_element.getElementsByTagName("system-out")[0].firstChild.nodeValue.strip() == stdout

        errors = test_case_element.getElementsByTagName("error")
        if error_message or error_output:
            assert len(errors) > 0
        else:
            assert len(errors) == 0

        if error_message:
            assert errors[0].attributes["message"].value == error_message

        if error_type and errors:
            assert errors[0].attributes["type"].value == error_type

        if error_output:
            assert errors[0].firstChild.nodeValue.strip() == error_output

        failures = test_case_element.getElementsByTagName("failure")
        if failure_message or failure_output:
            assert len(failures) > 0
        else:
            assert len(failures) == 0

        if failure_message:
            assert failures[0].attributes["message"].value == failure_message

        if failure_type and failures:
            assert failures[0].attributes["type"].value == failure_type

        if failure_output:
            assert failures[0].firstChild.nodeValue.strip() == failure_output

        skipped = test_case_element.getElementsByTagName("skipped")
        if skipped_message or skipped_output:
            assert len(skipped) > 0
        else:
            assert len(skipped) == 0
