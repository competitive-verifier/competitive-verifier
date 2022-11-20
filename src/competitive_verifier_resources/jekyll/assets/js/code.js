hljs.highlightAll()
for (const btn of document.getElementsByClassName('code-copy-btn')) {
    btn.addEventListener('click', async function () {
        const preText = this.closest('.code').querySelector('.pre-code:not(.disable) code').innerText
        navigator.clipboard.writeText(preText)

        this.classList.remove("hint--disable")
        await new Promise(r => setTimeout(r, 700))
        this.classList.add("hint--disable")
    })
}

for (const btn of document.getElementsByClassName('code-toggle-btn')) {
    btn.addEventListener('click', function () {
        for (const btn of document.getElementsByClassName('code-toggle-btn')) {
            btn.classList.remove('selected')
        }
        this.classList.add('selected')

        const targetId = this.dataset.target
        for (const pre of document.getElementsByClassName('pre-code')) {
            pre.classList.add('disable')
        }
        document.getElementById(targetId).classList.remove('disable')
    })
}
