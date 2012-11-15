//      Mindreader Application
//      (c) 2012 Joel Bohman


Mindreader = {};
Mindreader.current_position = null;
Mindreader.vent = _.extend({}, Backbone.Events);

// Vote
// ----
Mindreader.Vote = Backbone.Model.extend({
    urlRoot: '/api/message/vote/'
});

// Message
// -------

Mindreader.Message = Backbone.Model.extend({});


// MessageList
// -----------

Mindreader.MessageList = Backbone.Collection.extend({
    model: Mindreader.Message,
    url: '/api/message/',
    comparator: function(message) {
        return message.get('created');
    }
});


// SubMessageListView
// ------------------
Mindreader.SubMessageListView = Backbone.View.extend({
    tagName: 'ul',
    className: 'sub-message-list',

    message_form_template: _.template($('#message-form-template').html()),

    initialize: function(parent_id) {
        this.messages = new Mindreader.MessageList();
        this.parent_id = parent_id;
        this.messages.bind('add', this.add_one, this);
        this.messages.bind('reset', this.add_many, this);
        this.messages.bind('all', this.render, this);
        this.fetch(Mindreader.current_position);
    },

    fetch: function(position) {
        this.messages.fetch({data: $.param({latitude: position.coords.latitude,
                                            longitude: position.coords.longitude,
                                            parent: this.parent_id})});
    },

    toggle: function() {
        this.$el.toggle();
    },

    render: function() {
        //if (!_.has(this, 'message_form')) {
            //this.message_form = $(this.message_form_template());
            //this.message_form.insertAfter('.sub-message-list');
        //}
        return this;
    },

    add_one: function(message) {
        this.$el.prepend(new MessageView({model: message}).render().el);
    },

    add_many: function(messages) {
        messages.each(_.bind(this.add_one, this));
    },
});


// MessageView
// -----------

var MessageView = Backbone.View.extend({
    tagName: 'li',
    template: _.template($('#message-template').html()),

    events: {
        'click .more-info': 'click',
        'touchstart .more-info': 'click',
        'click .vote-handle': 'vote',
    },

    initialize: function() {
        this.model.bind('change', this.render, this);
        this.model.bind('destroy', this.remove, this);
    },

    render: function() {
        this.$el.attr('id', this.model.id);
        this.$el.html(this.template(this.model.toJSON()));
        return this;
    },

    vote: function(evt) {
        vote_type = false;
        if ($(evt.currentTarget).hasClass('vote-positive')) {
            vote_type = true;
        }

        var vote = new Mindreader.Vote({message_id: this.model.id, vote_type: vote_type});
        vote.bind('change:total_votes', function(vote) {
            this.model.set({votes: vote.get('total_votes')});
        }, this);
        vote.save({wait: true});
    },

    click: function(evt) {
        if (!_.has(this, 'answers')) {
            this.answers = new Mindreader.SubMessageListView(this.model.id);
            this.$el.append(this.answers.render().el);
        } else {
            this.answers.toggle();
        }
    }
});


// MessageListView
// ---------------

var MessageListView = Backbone.View.extend({
    el: $('.message-list'),
    messages: new Mindreader.MessageList(),
    message_ids: [],
    timeout: false,

    initialize: function() {
        this.messages.bind('add', this.add_one, this);
        this.messages.bind('reset', this.add_many, this);
        this.messages.bind('all', this.render, this);

        Mindreader.vent.on('position_update', _.bind(this.fetch, this));
        Mindreader.vent.on('save_message', _.bind(function(data) {
            this.messages.create(data, {wait: true});
        }, this));
    },

    fetch: function(position) {
        var success_callback = _.bind(function(collection, response) {
            var that = this;
            clearTimeout(this.timeout);
            this.timeout = setTimeout(function() { that.fetch(Mindreader.current_position) }, 10000);
        }, this);
        this.messages.fetch({success: success_callback, data: $.param({latitude: position.coords.latitude, longitude: position.coords.longitude})});
    },

    render: function(coordinates) {

    },

    add_one: function(message) {
        if (_.indexOf(this.message_ids, message.id) === -1) {
            this.$el.prepend(new MessageView({model: message}).render().el);
            this.message_ids.push(message.id);
        }
    },

    add_many: function(messages) {
        messages.each(_.bind(this.add_one, this));
    }
});


// FormView
// --------

var FormView = Backbone.View.extend({
    el: $('#message-form'),

    events: {
        'submit': 'save'
    },

    initialize: function() {
        this.$el.show();
    },

    save: function(a) {
        Mindreader.vent.trigger('save_message', {'latitude': Mindreader.current_position.coords.latitude,
                                                 'longitude': Mindreader.current_position.coords.longitude,
                                                 'message': this.$el.find('textarea').val()});
        this.$el.find('textarea').val('');
        return false;
    }
});

// AccuracyView
// ------------
Mindreader.AccuracyView = Backbone.View.extend({
    tagName: 'div',
    className: 'accuracy',
    template: _.template($('#accuracy-template').html()),

    initialize: function() {
        Mindreader.vent.on('position_update', _.bind(this.render, this));
    },

    render: function(position) {
        var accuracy = Math.ceil(position.coords.accuracy);
        this.$el.html(this.template({accuracy: accuracy}));
        if (accuracy < 100) {
            this.$el.css({
                width: (accuracy / 50) * 50,
                height: (accuracy / 50) * 50,
                lineHeight: (accuracy / 50) * 50 + 'px',
            });
        }
        if (accuracy < 25) {
            this.$el.removeClass('medium low').addClass('high');
        } else if (accuracy < 50) {
            this.$el.removeClass('high low').addClass('medium');
        } else if (accuracy < 100) {
            this.$el.removeClass('medium high').addClass('low');
        } else {
            // TODO: error...
            console.log('Too low accuracy...');
        }
        this.$el.insertAfter('h1');
    }
});


// ErrorView
// ---------

var ErrorView = Backbone.View.extend({
    template: _.template($('#error-template').html()),

    initialize: function() {},

    render: function(header, message) {
        var rendered = this.template({header: header, message: message});
        jQuery(rendered).insertAfter('h1');
    }
});

// InfoView
// ---------

var InfoView = Backbone.View.extend({
    template: _.template($('#info-template').html()),

    initialize: function() {},

    render: function(header, message) {
        var rendered = this.template({header: header, message: message});
        this.$el = jQuery(rendered).insertAfter('h1');
    },

    hide: function() {
        this.$el.remove();
    }
});


// ApplicationView
// ---------------

var ApplicationView = Backbone.View.extend({
    initialize: function() {
        if (Modernizr.geolocation) {
            this.welcome_info = new InfoView();
            // TODO: detect iOS or android and write a better message
            this.welcome_info.render('Your location is required!', 'For you to participate in the local hivemind you must enable us to access your location. This is required for us to partition you into the right hivemind which will serve you interesting thoughts from interesting people. We think you are using Google Chrome as your browser and therefor you need only to click "Allow" right up there below your address bar.');
            navigator.geolocation.watchPosition(_.bind(this.geolocation_position, this), _.bind(this.geolocation_error, this), {enableHighAccuracy: true, timeout: 10000, maxiumAge: 20000});
        } else {
            error_view = new ErrorView();
            // TODO: detect iOS or android and write a better message
            error_view.render('Geolocation Unavailable', 'Your device does not support Geolocation API. You could try our native iOS or Android Application.');
        }
    },

    geolocation_position: function(position) {
        this.welcome_info.hide();

        console.log(position);

        if (Mindreader.current_position === null) {
            this.message_list_view = new MessageListView();
            this.form_view = new FormView();
            this.accuracy_view = new Mindreader.AccuracyView();
        }

        Mindreader.current_position = position;

        // TODO: only trigger after delta change
        Mindreader.vent.trigger('position_update', position);
    },

    geolocation_error: function(error) {
        error_view = new ErrorView();
        switch (error.code) {
            case error.PERMISSION_DENIED:
                error_view.render('Permission Denied', 'You did not give your permission to use geolocation. This application requires the permission...');
                break;

            case error.POSITION_UNAVAILABLE:
                error_view.render('Position Unavailable', 'Could not retrieve your position for this device...');
                break;

            // TODO: after x timeouts print error maybe?
            case error.TIMEOUT:
                error_view.render('Timeout', '...');
                break;

            case error.UNKNOWN_ERROR:
                error_view.render('Unknown Error', '...');
                break;
        }
        console.log(error);
    }
});

var Application = new ApplicationView();


Mindreader.Router = Backbone.Router.extend({
    routes: {
        '' : 'index',
        'signup': 'signup',
        'message/:id': 'message',
        '*path': 'error_404'
    },

    index: function() {
        console.log(this, 'index');
    },

    signup: function() {
        console.log(this, 'signup');
    },

    message: function(message_id) {
        console.log(this, 'message');
    },

    error_404: function() {
        console.log(this, '404');
    }
});

var app_router = new Mindreader.Router();
var result = Backbone.history.start({pushState: true, root: '/'});
console.log(result);

  // All navigation that is relative should be passed through the navigate
  // method, to be processed by the router. If the link has a `data-bypass`
  // attribute, bypass the delegation completely.
  $(document).on('click', 'a:not([data-bypass])', function(evt) {
    // Get the absolute anchor href.
    var href = $(this).attr("href");

    // If the href exists and is a hash route, run it through Backbone.
    if (href && href.indexOf("#") === 0) {
      // Stop the default event to ensure the link will not cause a page
      // refresh.
      evt.preventDefault();

      // `Backbone.history.navigate` is sufficient for all Routers and will
      // trigger the correct events. The Router's internal `navigate` method
      // calls this anyways.  The fragment is sliced from the root.
      Backbone.history.navigate(href, true);
    }
  });
