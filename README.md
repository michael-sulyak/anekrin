# Anekrin

[![Scrutinizer Code Quality](https://img.shields.io/scrutinizer/g/expert-m/anekrin.svg?style=flat)](https://scrutinizer-ci.com/g/expert-m/anekrin/?branch=master)
[![GitHub Issues](https://img.shields.io/github/issues/expert-m/anekrin.svg?style=flat)](https://github.com/expert-m/anekrin/issues)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://choosealicense.com/licenses/apache-2.0/)

> Anekrin is an easy-to-use personal productivity tracker that helps you stay on top of your daily tasks and goals. With Anekrin, you can create a list of tasks and set rewards for each one, track your progress over the last seven days, and strive to keep your "average" productivity score at 100. Anekrin is the perfect companion for anyone looking to improve their daily routine and reach their goals. 
> Try Anekrin today and see the difference it can make in your life!

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
