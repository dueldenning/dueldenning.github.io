(function(window, lawfight, Redux, _, $, Handlebars) {

    // state control
    var state_control = function(state, action) {
        if (action.type === '@@redux/INIT') return;
        if (state === undefined && action.type !== 'CHANGE_FULL') {
            throw new Error('Illegal State Exception: CHANGE_FULL action should always be first. (' + action.type + ')');
        }

        if (action.type === 'CHANGE_OPTION') {
            state['options'][action.option_name] = action.option_value;
        } else if (action.type === 'ADD_CHAT_MSG') {
            state['chat'].push({
                'message': action.message,
                'username': action.username,
            });
        } else if (action.type === 'CHANGE_FULL') {
            // simple overwrie of options but merge of chat
            state = {}
            state.options = action.state.options;
            state.chat = _.union(state.chat || [], action.state.chat);
            state.task = action.state.task;
            state.assignments = action.state.assignments;
        }

        return state;
    };
    var state = Redux.createStore(state_control);

    // Data binder
    var update_draft = (function() {
        var draft_node = $('#draft .panel-body');
        var draft_template = Handlebars.compile(draft_node.text());
        return function(context) {
        	console.log('Update draft:', context);
            draft_node.html(draft_template(context));
        }
    })();

    // server comms
    var socket = io({
        'path': '/io',
        autoConnect: false,
    });
    socket.on('connect', function() {
        console.log('connect');
        socket.emit('join', {
            'task_name': lawfight.task_name,
            'room_id': lawfight.room_id,
        });
    });
    socket.on('state change', function(msg) {
        console.log('state change from server:', msg);
        state.dispatch({
            type: 'CHANGE_FULL',
            state: msg.new_state,
        });
    });
    socket.open(); // start it up

    // Chat
    var input = $('#chatbox-input');
    input.on('keydown', function(ev) {
        if (ev.keyCode !== 13) return;
        ev.preventDefault();
        var msg = input.val();
        if (msg === '') return;

        state.dispatch({
            type: 'ADD_CHAT_MSG',
            'username': lawfight.username,
            'message': msg,
        });
    });
    // options
    $('#options select').on('change', function(ev) {
        state.dispatch({
            type: 'CHANGE_OPTION',
            option_name: $(ev.target).data('option-name'),
            option_value: $(this).val(),
        });
    });

    // state change
    (function() {
        var last_state = {};
        state.subscribe(function() {
            var new_state = state.getState()

            if (_.isEqual(last_state, new_state)) {
                console.log('state the same');
                return;
            }
            console.log('state changed: ', last_state, new_state);
            last_state = new_state;

            _.each(new_state['options'], function(option_value, option_name) {
                console.log('state changed: ' + option_name, option_value);
                var node = $('#option_' + option_name);
                node.find('option').each(function() {
                    var option_node = $(this);
                    if (option_node.val() === option_value) {
                        option_node.attr('selected', 'true');
                    } else {
                        option_node.removeAttr('selected');
                    }
                });
            });

            var chatbox_node = $('#chatbox-log ol');
            chatbox_node.empty();
            _.each(new_state['chat'], function(chat) {
                var username = chat['username'];
                var msg = chat['message'];
                var msg_node = $('<li>').text(username + ': ' + msg);
                chatbox_node.append(msg_node);
            });

            update_draft(new_state['options']);

            var assignment = new_state['assignments'][lawfight.username];
            $('#brief .panel-body').html(new_state['task']['briefs'][assignment]);

            socket.emit('state change', {
                'new_state': new_state,
                'task_name': lawfight.task_name,
                'room_id': lawfight.room_id,
            });
        });
    })();

})(window, window.lawfight, window.Redux, window._, window.$, window.Handlebars);
