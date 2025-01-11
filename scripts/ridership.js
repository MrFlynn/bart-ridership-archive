export const config = {
    url: "https://www.bart.gov/news/articles/2025/news20250109-1",
}

export default function ({ doc, url, absoluteURL }) {
    var entries = {}
    const rows = doc.find("tr")

    rows.map(row => {
        const items = row.children()

        if (items.length % 2 == 0) {
            for (let i = 0; i < items.length; i += 2) {
                const date = items.get(i).text().trim()
                const ridership = Number.parseInt(items.get(i + 1).text().replace(",", ""))

                if (
                    date.match(/^([0-9]{1,2}\/){2}[0-9]{1,2}$/) !== null &&
                    ridership > 0
                ) {
                    entries[date] = {
                        riders: ridership,

                        // BART stopped providing this information in 2025. A filler
                        // value is provided to keep the data scheme the same.
                        percent_baseline: -1,
                    }
                }
            }
        }
    })

    return entries
}
