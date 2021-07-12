document.getElementById('save-btn').onclick = function() {
    const csrf_token = document.getElementsByName('csrfmiddlewaretoken')[0].value
    const xhttp = new XMLHttpRequest()

    xhttp.open('POST', '/editor/')
    xhttp.setRequestHeader('X-CSRFToken', csrf_token)
    xhttp.setRequestHeader('Content-type', 'application/json')
    
    const data = {
        'name': document.getElementsByName('name')[0].value,
        'description': document.getElementsByName('description')[0].value,
    }

    xhttp.send(JSON.stringify(data))
    document.getElementById('editor').submit()
}
