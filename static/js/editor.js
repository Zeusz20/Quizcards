/* DECK EDITING OPTIONS */
refreshDelete()   // refresh delete buttons

document.getElementById('new-card').onclick = () => {
    // add new card
    const container = document.getElementById('container')
    container.innerHTML += cardTemplate

    // refresh newly added delete button
    refreshDelete()
}

function refresh() {
    document.getElementsByName('delete-btn').forEach(btn => {
        // prevent reassignig onclick function to delete buttons
        if(btn.onclick == null) {
            btn.onclick = () => {
                const card = btn.parentElement
                btn.parentElement.parentElement.removeChild(card)
            }
        }
    })
}


/* TEXT FORMATTING OPTIONS */

const tools = document.getElementsByName('tool');
const colorPickers = document.getElementsByName('picker')

// apply standard formatting options
tools.forEach(tool => {
    tool.addEventListener('click', () => {
        document.execCommand(tool.dataset['command'], false, null)
        
        // get neighboring element nodes
        let neighbors = Array.from(btn.parentElement.parentElement.childNodes).filter(item => {
            return item.nodeType == Node.ELEMENT_NODE   // filters out text nodes
        })
        
        // get corresponding editor to the clicked formatting button
        let editor = neighbors.filter(element => {
            let name = element.getAttribute('name')
            return name == 'term' || name == 'definition'
        })[0]

        editor.focus()
    })
})

// apply color
colorPickers.forEach(picker => {
    picker.addEventListener('change', () => {
        document.execCommand('styleWithCSS', false,  true)
        document.execCommand('foreColor', false, picker.value)
    })
})