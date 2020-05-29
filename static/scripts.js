
document.addEventListener('DOMContentLoaded', function () {
    const channelList = document.querySelector('#channels');
    const msglist = document.querySelector('#messages');
    const userList = document.querySelector('#users');
    const sendbtn = document.querySelector('#send');
    const createChannelBtn = document.querySelector('#create-channel');
    const changeUsernameBtn = document.querySelector('#change-username');
    
    const socket = io.connect('https://'+ document.domain + ':' + location.port);

    const appendMessage =  (list, msg) => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${msg.timestamp}</span>  <span style="color:${msg.color}; font-weight:bold">${msg.username}</span>: ${msg.message}`
        list.append(li);
        scrollMessageContainerToBottom();
    }

    const scrollMessageContainerToBottom = () => {
        msgContainer = document.querySelector('#messages-container');
        msgContainer.scrollTop = msgContainer.scrollHeight;
    }

    const recreateMsgList = messages => {
        msglist.innerHTML = '';
        messages.forEach(msg => {
            appendMessage(msglist, msg)
        });
    }

    const appendChannel = (list, channel) => {
        const li = document.createElement('li');
        let isActiveLink = '';
        if (channel == currentChannel) {
            isActiveLink = 'link-active';
        };
        li.innerHTML = `<a href='#' class="link-channel ${isActiveLink}">${channel}</a>`;
        list.append(li);
    }

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
    
    const switchChannel = (currentChannel, newChannel) => {
        
        if (newChannel != currentChannel) {
            leaveChannel(currentChannel);
            joinChannel(newChannel);
            console.log(`new channel is ${newChannel}`);            
        };             
    };

    const joinChannel = (newChannel) => {
        socket.emit('join channel', {'channel': newChannel});
        console.log(`joining channel ${newChannel}`);
        currentChannel = newChannel;
    }

    const leaveChannel = (currentChannel) => {
        socket.emit('leave channel', {'channel': currentChannel});
    }

    const createChannel = () => {
        const channel = getChannelFromPrompt();
        socket.emit('new channel', {'channel': channel});
    }

    const getChannelFromPrompt = () => {
        const channel = prompt('Enter new channel name:');
        return channel;
    }

    const recreateUserList = users => {
        userList.innerHTML = '';
        users.forEach(user => {
            appendUser(userList, user);
        });
    }

    const appendUser = (list, user) => {
        const li = document.createElement('li');
        li.innerHTML = `<a href='#' class="link-user">🧑‍💻${user}</a>`;
        list.append(li);
    }

    const changeUsername = () => {
        socket.emit('logout');
        window.location.replace('/login');
    }

    const addNewMessage = function(event) {
        if (event) {
            event.preventDefault();
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

    sendbtn.addEventListener('click', addNewMessage);

    window.addEventListener('keydown', e => {
        if (e.keyCode == 13) {
            addNewMessage();
        };
    });

    createChannelBtn.addEventListener('click', createChannel);
    
    changeUsernameBtn.addEventListener('click', changeUsername);

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
        console.log('successfully reconnected!');      
    });

    socket.on('recreate lists', data => {
        recreateChannelList(data['channels']);
        recreateMsgList(data['messages']);
        recreateUserList(data['users']);
    });

    socket.on('append channel', data => {
        appendChannel(channelList, data['channel']);
    });
    
});