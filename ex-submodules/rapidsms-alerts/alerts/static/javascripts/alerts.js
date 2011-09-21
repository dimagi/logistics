

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
        alert.showhide_detail(false, function() { alert.exit_pending_mode(); });
      });

    this.pending_action_mode = false;
    this.action_commit_in_progress = false;
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
        alert._('_newcomment').before(alert.render_comment(data));
        alert._('newcomment').val('');

        alert._('addcomment').show();
        alert._('pleasewait').hide();
      }, 'json');
  }
  
  //force: true = don't animate
  //callback: call when animation is finished
  this.showhide_detail = function(force, callback) {
    this.set_toggle_text(this.detail_expanded);
    var transition = (this.detail_expanded ? 'slideDown' : 'slideUp');
    this._('alertdetail')[transition](force ? 0 : 'slow', callback);
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
    if (this.action_commit_in_progress)
      return;

    if (action == 'fu') {
      //action does not have a 'pending' stage -- commit immediately
      this.exit_pending_mode();
      this.highlight_action(action);
      this.commit_action(action);
    } else {
      this.enter_pending_mode(action);
    }
  }

  this.commit_action = function(action) {
    var action_comment = (this.pending_action_mode ? $.trim(this._('actioncomment').val()) : '');

    //prevent concurrent action-change ajax requests; or else might end up violating data integrity rules on the server
    this.action_commit_in_progress = true;
    this._('doaction').attr('disabled', 'disabled')

    var alert = this;
    $.post(URLS.takeaction, {alert_id: this.id, action: action, comment: action_comment}, function(data) {
        alert.update(data);
        if (alert.status != 'closed') {
          alert.render_status();
          alert.populate_comments();
          alert.exit_pending_mode();

          //only safe to reset this AFTER new 'action' links have been rendered
          alert.action_commit_in_progress = false;
          alert._('doaction').attr('disabled', '')
        } else {
          //dismiss alert
          alert.$div.slideUp();
        }
      }, 'json');
  }

  this.enter_pending_mode = function(action) {
    this.pending_action_mode = true;

    this.highlight_action(action);
    
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

    var alert = this;
    this._('doaction').unbind('click');
    this._('doaction').click(function() {
        alert.commit_action(action);
      });
    this._('cancelaction').unbind('click');
    this._('cancelaction').click(function() {
        if (alert.action_commit_in_progress)
          return;
        alert.exit_pending_mode();
      });
  }

  this.exit_pending_mode = function() {
    if (!this.pending_action_mode)
      return;
    this.pending_action_mode = false;

    this.highlight_action(null);

    if (this.detail_expanded) {
      this._('pendingaction').slideUp();
      this._('_newcomment').slideDown();
    } else {
      this._('pendingaction').hide();
      this._('_newcomment').show();
    }
  }

  this.highlight_action = function(action) {
    this._('actions').find('a').each(function(i, a) {
        var $a = $(a);
        $a.css('font-weight', $a.attr('id') == 'action-' + action ? 'bold' : 'normal');
      });
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


