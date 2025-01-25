export const config = {
    url: "https://www.bart.gov/news/articles/2025/news20250109-1",
}

function parseDate(date) {
    const parts = date.split("/").map(p => Number.parseInt(p))
    return new Date(2000 + parts[2], parts[0] - 1, parts[1])
}

function calculatePercentBaseline(date, riders) {
    // A list of target riders per day of week indexed to each
    // day of week in it's numeric representation 
    // (from Date.prototype.getDay).
    const targetRidersPerDayOfWeek = [
        102325, 382805, 409929, 408019, 401880, 404005, 152759
    ]

    return Math.trunc((riders / targetRidersPerDayOfWeek[date.getDay()]) * 100)
}

export default function ({ doc, _ }) {
    return doc.find("tr").map(
        row => row.children()
    ).flat().map((items) => {
        try {
            const date = parseDate(items.get(0).text().trim())
            const riders = Number.parseInt(items.get(1).text().replace(",", ""))

            if (date !== null && riders > 0) {
                return {
                    date: date.toISOString().split("T")[0],
                    riders: riders,
                    percent_baseline: calculatePercentBaseline(date, riders),
                }
            }
        } catch (_) {
            return null
        }
    }).reduce((accumulator, entry) => {
        if (entry !== null && entry !== undefined) {
            accumulator[entry.date] = {
                riders: entry.riders,
                percent_baseline: entry.percent_baseline,
            }
        }

        return accumulator
    }, {})
}
