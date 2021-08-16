const answers = document.getElementsByName('answer')

answers.forEach(answer => {
    answer.onclick = () => {
        if(answer.value == 'True') {
            success(answer)
            unbind()
        }
        else {
            fail(answer)
            success(findCorrect())
            unbind()
        }
    }
})

/* colors the respective node green */
function success(node) {
    node.classList.remove('btn-outline-secondary')
    node.classList.add('btn-success')
}

/* colors the respective node red */
function fail(node) {
    node.classList.remove('btn-outline-secondary')
    node.classList.add('btn-danger')
}

/* finds the correct answer node which matches the question */
function findCorrect() {
    for(let i=0; i < answers.length; i++) {
        const answer = answers[i]
        if(answer.value == 'True') {
            return answer
        }
    }

    return null
}

/* after answering unbind any functionality from answer nodes */
function unbind() {
    answers.forEach(button => button.onclick = null)
}