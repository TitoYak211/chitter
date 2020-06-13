
document.addEventListener('DOMContentLoaded', function () {
    const channelList = document.querySelector('#channels');
    const messageList = document.querySelector('#messages');
    const userList = document.querySelector('#users');
    const sendButton = document.querySelector('#send');
    const createChannelButton = document.querySelector('#create-channel');
    const changeUsernameButton = document.querySelector('#change-username');
    const messageContainer = document.querySelector('#messages-container');
    
    // Connect to websocket
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port, {transports: ['polling']});

    const appendMessage = (lst, message) => {
        // Create message box
        const li = document.createElement('li');

        li.innerHTML = `<span>${message.timestamp}</span>  <span style="color:${message.color}; font-weight:bold">${message.username}</span>: ${message.message}`;

        // Add message to the list
        lst.append(li);

        // Auto scroll to see most recent message
        scrollToBottom();
    }

    // Auto scroll function
    const scrollToBottom = () => {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    // Recreate message list per session
    const recreateMessageList = messages => {
        messageList.innerHTML = '';

        messages.forEach(message => {
            appendMessage(messageList, message)
        });
    }

    const appendChannel = (lst, channel) => {
        const li = document.createElement('li');

        let isActiveLink = '';

        if (channel == currentChannel) {
            isActiveLink = 'link-active';
        };

        li.innerHTML = `<a href='#' class="link-channel ${isActiveLink}">${channel}</a>`;

        lst.append(li);
    }

    // Recreate channel list per session
    const recreateChannelList = channels => {
        channelList.innerHTML = '';

        channels.forEach(channel => {
            appendChannel(channelList, channel);
        });

        updateChannelLinkListeners();
    }

    const updateChannelLinkListeners = function() {
        const channelLinks = document.querySelectorAll('.link-channel');

        channelLinks.forEach(link => {
            const newChannel = link.innerHTML;

            link.addEventListener('click', () => {
                switchChannel(currentChannel, newChannel);
            });
        });
    };
    
    // Changing current channel
    const switchChannel = (currentChannel, newChannel) => {
        if (newChannel != currentChannel) {
            leaveChannel(currentChannel);

            joinChannel(newChannel);      
        };             
    };

    // Joining a channel
    const joinChannel = (newChannel) => {
        socket.emit('join channel', { 'channel': newChannel });

        currentChannel = newChannel;
    }

    // Leaving a channel
    const leaveChannel = (currentChannel) => {
        socket.emit('leave channel', {'channel': currentChannel});
    }

    // Create a new channel
    const createChannel = () => {
        const channel = getChannelFromPrompt();

        socket.emit('new channel', {'channel': channel});
    }

    const getChannelFromPrompt = () => {
        const channel = prompt('Enter new channel name:');

        return channel;
    }

    // Recreate user list per session
    const recreateUserList = users => {
        userList.innerHTML = '';

        users.forEach(user => {
            appendUser(userList, user);
        });
    }

    const appendUser = (lst, user) => {
        const li = document.createElement('li');

        li.innerHTML = `<a href='#' class="link-user">🧑‍💻${user}</a>`;

        lst.append(li);
    }

    const changeUsername = () => {
        socket.emit('logout');

        window.location.replace('/login');
    }

    const addNewMessage = e => {
        if (e) {
            e.preventDefault();
        }
        
        const message = document.querySelector('#m').value;

        if (message != '') {
            socket.emit('new message', {'message': message});       
            
            document.querySelector('#m').value = '';
        };
        
        return false;
    };

    window.addEventListener('beforeunload', () => {
        socket.disconnect();
    });

    sendButton.addEventListener('click', addNewMessage);

    window.addEventListener('keydown', e => {
        if (e.keyCode == 13) {
            addNewMessage();
        };
    });

    createChannelButton.addEventListener('click', createChannel);
    
    changeUsernameButton.addEventListener('click', changeUsername);

    socket.on('get channel name',  () => {
        if (!localStorage.getItem('current_channel')) {
            localStorage.setItem('current_channel', 'global');
        };

        currentChannel = localStorage.getItem('current_channel');
        
        socket.emit('receive channel name', {'channel': currentChannel});
    });

    socket.on('disconnect', () => {
        localStorage.setItem('current_channel', currentChannel);
    });

    socket.on('reconnect',  () => {
        localStorage.setItem('current_channel', currentChannel);      
    });

    socket.on('recreate lists', data => {
        recreateChannelList(data['channels']);

        recreateMessageList(data['messages']);
        
        recreateUserList(data['users']);
    });

    socket.on('append channel', data => {
        appendChannel(channelList, data['channel']);
    });
    
});
