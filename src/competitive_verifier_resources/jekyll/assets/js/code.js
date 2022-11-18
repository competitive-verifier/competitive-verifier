hljs.highlightAll()
$('.code-copy-btn').on('click', async function () {
    var preText = $(this).closest(".code").find(".pre-code.enabled code").text()
    navigator.clipboard.writeText(preText)

    $(this).showBalloon()
    await new Promise(r => setTimeout(r, 300))
    $(this).hideBalloon()
});

$('.code-toggle-btn').on('click', function () {
    $('.code-toggle-btn').removeClass('selected')
    $(this).addClass('selected')

    targetId = $(this).data('target')
    $('.pre-code').removeClass('enabled')
    $(`#${targetId}`).addClass('enabled')
});