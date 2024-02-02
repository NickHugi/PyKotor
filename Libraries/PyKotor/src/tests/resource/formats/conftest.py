#def pytest_report_teststatus(report, config):
#    if report.when == 'call' and report.failed:
#        return report.outcome, 'F', 'FAILED'
#    if report.when == 'call':
#        return report.outcome, '', ''
#    return None