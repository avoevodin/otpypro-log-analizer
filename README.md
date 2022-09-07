- [Log Analyzer](#log-analyzer)
    + [Nginx log analyzer.](#nginx-log-analyzer)
- [Installing](#installing)
- [Configuring](#configuring)
    + [Description of some configs:](#description-of-some-configs-)
- [Development and testing](#development-and-testing)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

# Log Analyzer

### Nginx log analyzer.
Get some statistics from logs and put it to html-report

# Installing

* Clone the rep:
```shell
git clone git@github.com:avoevodin/otpypro-log-analyzer.git
```
* Go to the root of the cloned rep
* Install pipenv:
```shell
pip install pipenv
```
* Activate pipenv shell:
```shell
pipenv shell
```
* Install dependencies:
```shell
pipenv install
```
* Run with default config file:
```shell
python3 -m log_analyzer.py
```
* Or run with you custom config file:
```shell
python3 -m log_analyzer.py --conf 'path/to/your/config_file.json' 
```

# Configuring
* Ensure, that you have a config.json file in the project directory. It may be for example:
```json
{
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOGS_FILENAME": "exec_logs",
    "LOG_LEVEL": "DEBUG",
    "DATA_ENCODING": "UTF-8"
}
```
### Description of some configs:
1. REPORT_SIZE - max amount of report lines.
2. REPORT_DIR - path to the dir, where reports should be stored.
3. LOG_DIR - path to the dir with nginx logs. 
Exec logs will be stored at the same place.
4. LOGS_FILENAME - filename for the execution logs. If None, logs
will be shown with stdout.
5. LOG_LEVEL - the level of logging information.
6. DATA_ENCODING - encoding of IO data.

# Development and testing

* Install dev dependencies:
```shell
pipenv install --dev
```
* Running test logs generation
> Logs will be generated into the directory 
> specified at the LOG_DIR config.
```shell
python3 create_test_logs.py -c AMOUNT_OF_LOG_FILES -r AMOUNT_OF_RECORDS_IN_EACH_FILE
```
* Running tests:
```shell
coverage run -m unittest tests.py -v
```
* Generate coverage html-report:
```shell
coverage html -d cov-report
```
* Open generated report:
```shell
open cov-report/index.html
```
