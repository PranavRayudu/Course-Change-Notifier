export default function ({count, word, plural}) {
    return (count === 1 ? word : plural || word + 's')
}
