hljs.highlightAll()
$('.code-copy-btn').on('click', async function () {
    var preText = $(this).closest(".code").find(".pre-code code").text()
    navigator.clipboard.writeText(preText)

    $(this).showBalloon()
    await new Promise(r => setTimeout(r, 300))
    $(this).hideBalloon()
});

(function () {
    const unbundle = function () {
        $('#unbundled').each(function (index, element) {
            $(element).parent().next().show();
        });
        $('#bundled').each(function (index, element) {
            $(element).parent().next().hide();
        });
        $('.code-bundle-btn').each(function (index, element) {
            $(element).text("Bundle");
        });
    };
    const bundle = function () {
        $('#unbundled').each(function (index, element) {
            $(element).parent().next().hide();
        });
        $('#bundled').each(function (index, element) {
            $(element).parent().next().show();
        });
        $('.code-bundle-btn').each(function (index, element) {
            $(element).text("Unbundle");
        });
    };
    // bundle されたコードは最初は非表示に
    let is_bundled = false;
    unbundle();
    $('.code-bundle-btn').on('click', function () {
        // bundle / unbundle の切り替え
        if (is_bundled) {
            unbundle();
        } else {
            bundle();
        }
        is_bundled = !is_bundled;
    });
})()