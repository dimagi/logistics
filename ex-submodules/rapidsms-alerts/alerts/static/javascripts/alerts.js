

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
    this.render_status();

    this.detail_expanded = false;
    this.showhide_detail(true);
    var alert = this;
    this._('toggle').click(function() {
        alert.detail_expanded = !alert.detail_expanded;
        alert.showhide_detail();
      });

    this._('pendingaction').hide();
  }

  this.populate_comments = function() {
    this.num_comments = 0;
    var $comments = this._('comments');
    $comments.empty();
    var alert = this;
    $(this.comments).each(function (i, comment) {
        var $comment = alert.render_comment(comment);
        $comments.append($comment);
      });
    $comments.append('<div id="_newcomment"><input id="newcomment" style="width: 30em;"> <a id="addcomment" href="#">add comment</a><span id="pleasewait">please wait&hellip;</span></div>');
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
    this.set_toggle_text(this.detail_expanded);
    var transition = (this.detail_expanded ?
                      (force ? 'show' : 'slideDown') :
                      (force ? 'hide' : 'slideUp'));
    this._('alertdetail')[transition]();
  }

  this.set_toggle_text = function(expanded) {
    var caption = (expanded ? 'hide' : 'show ' + (this.num_comments > 0 ? 'comments(' + this.num_comments + ')' : 'history'));
    this._('toggle').text(caption);
  }

  this.render_status = function() {
    var status_text = {
      'new': function(a) { return 'new'; },
      'fu': function(a) { return a.owner + ' is following up'; },
      'esc': function(a) { return 'escalated to ' + a.owner; },
      'closed': function(a) { return 'closed'; },
    }[this.status](this);
    this._('status').text(status_text);

    var $actions = this._('actions');
    $actions.empty();
    var alert = this;
    $(this.actions).each(function(i, action) {
        var $action = $('<a id="action-' + action + '" href="#">' + alert.action_caption(action) + '</a>');
        $action.click(function() { alert.pending_action(action); });
        $actions.append($action);
        if (i < alert.actions.length - 1) {
          $actions.append(' &middot; ');
        }
      });
  }

  this.pending_action = function(action) {
    if (action == 'fu') {
      this.commit_action(action);
    } else {
      this.enter_pending_mode(action);
    }
  }

  this.commit_action = function(action) {
    var alert = this;
    $.post(URLS.takeaction, {alert_id: this.id, action: action}, function(data) {
        alert.update(data);
        if (alert.status != 'closed') {
          alert.render_status();
          alert.populate_comments();
        } else {
          //dismiss alert
          alert.$div.slideUp();
        }
      }, 'json');
  }

  this.enter_pending_mode = function(action) {
    this._('action-' + action).css('font-weight', 'bold');

    this._('doaction').text(this.action_caption(action));
    this._('commentsnippet').text({
        'resolve': 'how this alert was resolved',
        'esc': 'why this alert is being escalated',
      }[action]);

    if (this.detail_expanded) {
      this._('pendingaction').slideDown();
      this._('_newcomment').slideUp();
    } else {
      this._('pendingaction').show();
      this._('_newcomment').hide();
      this.detail_expanded = true;
      this.showhide_detail();
    }

  }

  //only updates values naively; UI and calculated values (i.e., # comments) must be updated/maintained separately
  this.update = function(raw) {
    for (var k in raw) {
      this[k] = raw[k];
    }
  }

  this._ = function(id, root) {
    return (root == null ? this.$div : root).find('#' + id);
  }

  this.action_caption = function(action) {
    return {
      'fu': 'follow up',
      'resolve': 'resolve',
      'esc': 'escalate',
    }[action];
  };

  this.init();
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

