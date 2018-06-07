# update four table, pid = type_aliases + id + ptid

UPDATE activity_ticket SET activity_ticket.pid = CONCAT('at', id, COALESCE(`ptid`, ''));
UPDATE play_ticket SET play_ticket.pid = CONCAT('pt', id, COALESCE(`ptid`, ''));
UPDATE tour_ticket SET tour_ticket.pid = CONCAT('tour', id, COALESCE(`ptid`, ''));
UPDATE view_ticket SET view_ticket.pid = CONCAT('vt', id, COALESCE(`ptid`, ''));


# update tickets_fun, pid = another.pid where local.id_3th = another.pid
UPDATE tickets_fun tf, activity_ticket other SET tf.pid = other.pid WHERE tf.id_3rd = other.id_3rd;
UPDATE tickets_fun tf, play_ticket other SET tf.pid = other.pid WHERE tf.id_3rd = other.id_3rd;
UPDATE tickets_fun tf, tour_ticket other SET tf.pid = other.pid WHERE tf.id_3rd = other.id_3rd;
UPDATE tickets_fun tf, view_ticket other SET tf.pid = other.pid WHERE tf.id_3rd = other.id_3rd;
