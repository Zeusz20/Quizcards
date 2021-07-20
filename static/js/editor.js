// ask the user before leaving
var warn = true

// start editor
init()


function init() {
    window.onload = warnUser

    if(rawDeck !== '' && rawCards !== '') {
        const deck = JSON.parse(rawDeck)
        const cards = JSON.parse(rawCards)
        load(deck, cards)
    }
    updateButtons()
}

function warnUser() {
    window.addEventListener('beforeunload', (event) => {
        if(warn) {
            let msg = 'Are you sure you want to leave?'
            event.returnValue = msg
            window.event.returnValue = msg
            return msg
        }
    })
}


/* DECK EDITING */

function addNewCard() {
    const container = document.getElementById('container')
    let template = document.createElement('template')
    template.innerHTML = cardTemplate.trim()
    container.appendChild(template.content.firstChild)
    updateButtons()
}

function updateButtons() {
    updateSaveButton()
    updateDeleteButton()
    updateFormattingButtons()
    updateColorPickers()
    updateImageButtons('term')
    updateImageButtons('definition')

    document.getElementById('new-card').onclick = addNewCard
}

function updateSaveButton() {
    // cannot save until user typed in deck's name
    const deckName = document.getElementById('name')
    const saveBtn = document.getElementById('save-btn')

    deckName.addEventListener('keyup', () => {
        saveBtn.disabled = (deckName.value === '')
    })

    saveBtn.onclick = save
}

function updateDeleteButton() {
    document.getElementsByName('delete-btn').forEach(btn => {
        btn.onclick = () => {
            const card = btn.parentElement
            btn.parentElement.parentElement.removeChild(card)
        }
    })
}

function updateFormattingButtons() {
    document.getElementsByName('tool').forEach(tool => {
        tool.addEventListener('click', () => {
            document.execCommand(tool.dataset['command'], false, null)
            
            // get neighboring element nodes
            let neighbors = Array.from(tool.parentElement.parentElement.childNodes).filter(element => {
                return element.nodeType == Node.ELEMENT_NODE   // filters out text nodes
            })
            
            // get corresponding editor to the clicked formatting button
            let editor = neighbors.filter(element => {
                let name = element.getAttribute('name')
                return name == 'term' || name == 'definition'
            })[0]
    
            editor.focus()
        })
    })
}

function updateColorPickers() {
    document.getElementsByName('picker').forEach(picker => {
        picker.addEventListener('change', () => {
            document.execCommand('styleWithCSS', false,  true)
            document.execCommand('foreColor', false, picker.value)
        })
    })
}

function updateImageButtons(type) {
    const imageName = type + '-image'
    const previewName = type + '-preview'
    const deleteBtnName = 'del-' + type + '-img'

    hideAndShowImageControls(imageName, previewName, deleteBtnName)

    // image upload
    document.getElementsByName(imageName).forEach(input => {
        input.onchange = () => {
            if(input.files) {
                // get corresponging image preview node
                const img = Array.from(input.parentElement.childNodes).filter(element => element.name == previewName)[0]
                img.src = URL.createObjectURL(input.files[0])
            }
            hideAndShowImageControls(imageName, previewName, deleteBtnName)
        }
    })

    // image delete
    document.getElementsByName(deleteBtnName).forEach(btn => {
        btn.onclick = () => {
            // get corresponding image input and preview
            const file = Array.from(btn.parentElement.childNodes).filter(element => element.name == imageName)[0]
            const preview = Array.from(btn.parentElement.childNodes).filter(element => element.name == previewName)[0]
            file.value = '';
            preview.src = '';
            hideAndShowImageControls(imageName, previewName, deleteBtnName)
        }
    })
}

function hideAndShowImageControls(imageName, previewName, deleteBtnName) {
    let imageInputs = Array.from(document.getElementsByName(imageName))
    let imagePreviews = Array.from(document.getElementsByName(previewName))
    let deleteBtns = Array.from(document.getElementsByName(deleteBtnName))

    const imageFormattingControls = imagePreviews.map((item, index) => {
        // zip file upload, image preview nodes and image delete buttons
        return {
            'input': imageInputs[index],
            'controls': {
                'preview': item,
                'delete': deleteBtns[index]
            }
        }
    })

    // enable/disable preview and delete button depending on choosen image
    imageFormattingControls.forEach(pair => {
        let visibility = (pair.controls.preview.getAttribute('src') === '') ? 'hidden' : 'visible'
        Object.values(pair.controls).forEach(element => element.style.visibility = visibility)

        // invert visibility for input
        pair.input.style.visibility = (visibility == 'hidden') ? 'visible' : 'hidden'
    })
}


/* SAVE AND LOAD */

function save() {
    warn = false
    const form = document.getElementById('editor')

    // disable color pickers so they are not sent with POST
    Array.from(document.getElementsByTagName('input'))
        .filter(element => element.getAttribute('type') == 'color')
        .forEach(input => input.removeAttribute('name'))

    // initialize deck data
    const deck = document.createElement('input')
    deck.setAttribute('type', 'hidden')
    deck.setAttribute('name', 'deck')
    deck.setAttribute('value', getDeckJson())
    form.appendChild(deck)
    form.submit()
}

function getDeckJson() {
    const deck = {
        'name': document.getElementById('name').value,
        'description': document.getElementById('description').value,
        'uuid': document.getElementById('uuid').value,
        'cards': []
    }

    document.getElementsByName('card').forEach(element => {
        let term = Array.from(element.getElementsByTagName('div')).filter(div => div.getAttribute('name') == 'term')[0]
        let definition = Array.from(element.getElementsByTagName('div')).filter(div => div.getAttribute('name') == 'definition')[0]
        let images = Array.from(element.getElementsByTagName('input')).filter(input => input.getAttribute('type') == 'file')

        const card = {
            'term': term.innerHTML,
            'term_image': (images[0].value !== ''),     // has term image
            'definition': definition.innerHTML,
            'definition_image': (images[1].value !== '')    // has definition image
        }

        deck.cards.push(card)
    })

    return JSON.stringify(deck)
}

function load(deck, cards) {
    document.getElementById('save-btn').disabled = false

    // fill in deck data
    document.getElementById('name').value = deck.fields.name
    document.getElementById('description').value = deck.fields.description

    // fill in cards data
    let terms = Array.from(document.getElementsByName('term'))
    let definitions = Array.from(document.getElementsByName('definition'))

    // fill in image data
    let term_previews = Array.from(document.getElementsByName('term-preview'))
    let definition_previews = Array.from(document.getElementsByName('definition-preview'))

    for(let i = 0; i < terms.length; i++) {
        terms[i].innerHTML = cards[i].fields.term
        term_previews[i].src = loadImage(cards[i].fields.term_image)
    
        definitions[i].innerHTML = cards[i].fields.definition
        definition_previews[i].src = loadImage(cards[i].fields.definition_image)
    }
}

function loadImage(src) {
    return (src === '') ? src : window.location.origin + '/' + src
}