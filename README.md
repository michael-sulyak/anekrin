# aiohttp-rpc

[![Scrutinizer Code Quality](https://img.shields.io/scrutinizer/g/expert-m/anekrin.svg?style=flat)](https://scrutinizer-ci.com/g/expert-m/anekrin/?branch=master)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/expert-m/anekrin.svg?style=flat)](https://lgtm.com/projects/g/expert-m/anekrin/alerts/)
[![GitHub Issues](https://img.shields.io/github/issues/expert-m/anekrin.svg?style=flat)](https://github.com/expert-m/anekrin/issues)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://choosealicense.com/licenses/apache-2.0/)

> Anekrin is a simple task manager for evaluating personal performance.

## Table Of Contents
- **[Introduction](#Introduction)**
- **[To Do](#to-do)**
- [License](#license)

## Architecture

* One instance handles requests from specific users, and one instance has its own task queue for each user. That is, requests from certain users are processed sequentially and on a certain instance.

* At the current time, adding a DB for the cache does not make sense. The data can be kept in memory for now.

[back to top](#table-of-contents)

---

## To Do

* ✅ Implement PoC;
* ⬜️ Write tests for basic functional.


[back to top](#table-of-contents)

---

## License
Apache License 2.0
