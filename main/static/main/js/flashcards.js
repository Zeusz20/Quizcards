init()


function init() {
    shortcuts.getElementsByLabel('card').forEach(card => fillCardFace(card))
    document.getElementsByClassName('carousel-item')[0].classList.add('active')
    bindRotation()
}

function startWith() {
    const start = document.getElementsByName('start-with')[0].value
    return (start === '') ? 'term' : start
}

function getCard(child) {
    return (child.parentElement.getAttribute('data-label') == 'card') ? child.parentElement : getCard(child.parentElement)
}

function bindRotation() {
    document.getElementsByName('rotate-btn').forEach(button => {
        // TODO: 3d rotation
        Node.prototype.flipped = false     // saves rotation for each card

        button.onclick = () => {
            button.flipped = !button.flipped
            fillCardFace(getCard(button), button.flipped)
        }
    })
}

function fillCardFace(card, flipped=false) {
    const term = getCardFace(card, 'term')
    const definition = getCardFace(card, 'definition')

    // conditions that need to be fulfilled in order to display the card's term, otherwise display the card's definition
    let termDisplayConditions = (startWith() == 'term' && !flipped) || (startWith() == 'definition' && flipped)

    if(termDisplayConditions) {
        // display term
        shortcuts.showElement(term)
        shortcuts.hideElement(definition)
    }
    else {
        // display definition
        shortcuts.showElement(definition)
        shortcuts.hideElement(term)
    }
}

function getCardFace(card, name) {
    return shortcuts.getAllChildNodes(card).filter(child => child.getAttribute('data-label') == name)[0]
}
