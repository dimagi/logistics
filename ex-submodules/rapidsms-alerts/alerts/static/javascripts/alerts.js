

function Alert (div, raw_data) {
  this.init = function() {
    this.$div = div;
    this.update(raw_data);
  }

  this.init_render = function() {
    this._('msg').text(this.msg);
    this._('detail').toggle(Boolean(this.url));
    this._('url').attr('href', this.url);
    
    this.populate_comments();

    this.detail_expanded = false;
    this.showhide_detail(true);
    var alert = this;
    this._('toggle').click(function() {
        alert.detail_expanded = !alert.detail_expanded;
        alert.showhide_detail();
      });
  }

  this.populate_comments = function() {
    this.num_comments = 0;
    var $comments = this._('comments');
    var alert = this;
    $(this.comments).each(function (i, comment) {
        var $comment = alert.render_comment(comment);
        $comments.append($comment);
      });
    $comments.append('<input id="newcomment" style="width: 30em;"> <a id="addcomment" href="#">add comment</a><span id="pleasewait">please wait&hellip;</span>');
    this._('pleasewait').hide();
    var alert = this;
    this._('addcomment').click(function () { alert.add_comment(); });
  }

  this.render_comment = function(comment) {
    var $comment = $('<div><span id="text"></span> <span style="color: #d77;">by</span> <span id="author"></span> <span style="color: #d77;">at</span> <span id="date"></span></div>');
    if (comment.is_system) {
      $comment.css('background-color', '#ccf');
    }
    this._('text', $comment).text(comment.text);
    this._('author', $comment).text(comment.author);
    this._('date', $comment).text(comment.date_fmt);
    if (!comment.is_system) {
      this.num_comments++;
    }
    return $comment;
  }

  this.add_comment = function() {
    var comment_text = $.trim(this._('newcomment').val());
    if (!comment_text)
      return;

    this._('addcomment').hide();
    this._('pleasewait').show();
    var alert = this;
    $.post(URLS.addcomment, {alert_id: this.id, text: this._('newcomment').val()}, function(data) {
        alert._('newcomment').before(alert.render_comment(data));
        alert._('newcomment').val('');

        alert._('addcomment').show();
        alert._('pleasewait').hide();
      }, 'json');
  }
  
  this.showhide_detail = function(force) {
    var $detail = this._('alertdetail');
    var $toggle = this._('toggle');

    var toggle_text = function(expanded) {
      var caption = (expanded ? 'hide' : 'show ' + (this.num_comments > 0 ? 'comments(' + this.num_comments + ')' : 'history'));
      $toggle.text(caption);
    }

    toggle_text(this.detail_expanded);
    var transition = (this.detail_expanded ?
                      (force ? 'show' : 'slideDown') :
                      (force ? 'hide' : 'slideUp'));
    $detail[transition]();
  }

  //only updates values naively; UI and calculated values (i.e., # comments) must be updated/maintained separately
  this.update = function(raw) {
    for (var k in raw) {
      this[k] = raw_data[k];
    }
  }

  this._ = function(id, root) {
    return (root == null ? this.$div : root).find('#' + id);
  }

  this.init();
}

function render_alert(alert) {

  render_status(alert);


  $div.find('#pendingaction').toggle(false);

}



function render_status(alert) {
  var status_text = {
    'new': function() { return 'new'; },
    'fu': function() { return alert.owner + ' is following up'; },
    'esc': function() { return 'escalated to ' + alert.owner; },
    'closed': function() { return 'closed'; },
  }[alert.status]();
  this._('status').text(status_text);

  var $actions = this._('actions');
  $actions.empty();
  $(alert.actions).each(function(i, action) {
    var action_caption = {
      'fu': 'follow up',
      'resolve': 'resolve',
      'esc': 'escalate',
    }[action];
    var $action = $('<a href="#">' + action_caption + '</a>');
    $action.click(function() { pending_action(alert, action); });
    $actions.append($action);
    if (i < alert.actions.length - 1) {
      $actions.append(' &middot; ');
    }
  });
}

function pending_action(alert, action) {
  var $pend = this._('pendingaction');
  $pend.slideToggle(true);
}

function take_action(alert, action) {
  $.post('{% url alerts.ajax.alert_action %}', {alert_id: alert.id, action: action}, function(data) {
    var mod_alert = clone_alert(alert, data);
    if (mod_alert.status != 'closed') {
      render_status(mod_alert);
    } else {
      mod_alert.div.slideUp();
    }
  }, 'json');
}

