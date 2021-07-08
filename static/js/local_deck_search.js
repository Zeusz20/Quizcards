document.getElementById('local-deck-search').addEventListener('keyup', event => {
    let query = event.target.value.toLowerCase()

    let filtered = data.filter(deck => {
        let ignoreCaseName = deck.fields.name.toLowerCase()
        let ignoreCaseDescription = deck.fields.description.toLowerCase()
        return ignoreCaseName.includes(query) || ignoreCaseDescription.includes(query)
    })
    
    const holder = document.getElementById('holder')
    holder.innerHTML = ""

    if(filtered.length == 0) {
        holder.innerHTML = '<p class="text-muted">No results found.</p>'
    }
    else {
        // add matching decks
        filtered.forEach(deck => {
            // necessary formatting otherwise chaos ensues (chaining functions doesn't work either)
            let formatted = template.replaceAll('{{ ', '')
            formatted = formatted.replaceAll(' }}', '')
            
            // replace placeholders with actual values
            formatted = formatted.replaceAll('deck.pk', deck.pk)
                .replaceAll('deck.fields.name', deck.fields.name)
                .replaceAll('deck.fields.description', deck.fields.description)
                .replaceAll('deck.fields.date_created', deck.fields.date_created)
                .replaceAll('deck.fields.last_modified', deck.fields.last_modified)
            
            holder.innerHTML += formatted
        })
    }   
})