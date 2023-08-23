$(document).ready(function () {
    $('#model-form').submit(function (event) {
        event.preventDefault();

        $('#train-model-status-message').text('Training in progress...');
        $('#train-model-output-message').html('');

        $.ajax({
            url: '/model-selection',
            type: 'POST',
            data: $(this).serialize(),
            success: function (response) {
                if (response.status === 'success') {
                    $('#train-model-status-message').text('Training completed!');
                    $('#train-model-output-message').html(response.message.replace(/\n/g, '<br>'));
                } else {
                    $('#train-model-status-message').text('Error: ' + response.message);
                    $('#train-model-output-message').html('');
                }
                // Clear messages after 5 seconds
                setTimeout(function () {
                    $('#train-model-status-message').text('');
                    $('#train-model-output-message').text('');
                }, 5000);
            },
            error: function (xhr, textStatus, errorThrown) {
                $('#train-model-status-message').text('Error occurred during training');
                $('#train-model-output-message').html(xhr.responseText.replace(/\n/g, '<br>') || 'Unknown error');
                // Clear messages after 5 seconds
                setTimeout(function () {
                    $('#train-model-status-message').text('');
                    $('#train-model-output-message').text('');
                }, 5000);
            }
        });
    });
});
