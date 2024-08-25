export const config = {
    url: "https://www.bart.gov/news/articles/2023/news20230729",
}

export default function ({ doc, url, absoluteURL }) {
    var entries = {}
    const rows = doc.find("tr")

    rows.map(row => {
        const items = row.children()

        if (items.length % 3 == 0) {
            for (let i = 0; i < items.length; i += 3) {
                const date = items.get(i).text().trim()
                const ridership = Number.parseInt(items.get(i + 1).text().replace(",", ""))
                const percent = items.get(i + 2).text().trim()

                if (
                    date.match(/^([0-9]{1,2}\/){2}[0-9]{1,2}$/) !== null &&
                    (ridership != 0 || ridership !== null || ridership !== undefined) &&
                    (percentMatch = percent.match(/^([0-9]{1,3})%$/)) !== null 
                ) {
                    entries[date] = {
                        ridership: ridership, 
                        percent_baseline: Number.parseInt(percentMatch[0]),
                    }
                }
            }
        }
    })

    return entries
}
