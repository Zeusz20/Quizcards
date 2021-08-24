init()


function init() {
    document.getElementsByName('card').forEach(card => fillCardFace(card))
    document.getElementsByClassName('carousel-item')[0].classList.add('active')
    bindRotation()
}

function startWith() {
    const start = document.getElementsByName('start-with')[0].value
    return (start === '') ? 'term' : start
}

function getCard(child) {
    return (child.parentElement.getAttribute('name') == 'card') ? child.parentElement : getCard(child.parentElement)
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
    const term = getCardElement(card, 'term')
    const definition = getCardElement(card, 'definition')

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

function getCardElement(card, name) {
    return Array.from(card.getElementsByTagName('div')).filter(div => div.getAttribute('name') == name)[0]
}
