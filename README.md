# BART Ridership Archive

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/MrFlynn/e734700d586151d29d8da4b56639d8d7/raw/riders.json)

An automatic, daily backup of ridership data from BART (Bay Area Rapid Transit)
saved as a JSON file. 

## How it Works
BART (usually) updates a table on 
[this page](https://www.bart.gov/news/articles/2020/news20200225) with daily
ridership numbers. This repository contains [a script](scripts/ridership.js)
that is executed with [flyscrape](https://github.com/philippta/flyscrape)
that parses the tables on this page and saves data to a JSON file called
`ridership.json`. This file can then be used for analyzing ridership trends, etc.

## License and Credit
The source code in this repository is licensed under the [MIT](LICENSE) license.

Ridership data is sourced from the [Bay Area Rapid Transit District](bart.gov).
