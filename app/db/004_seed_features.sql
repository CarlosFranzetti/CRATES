-- Crates: demo seed for 003 features (owner 'demo'; idempotent). Statements separated by "-- ;;".

update units set qr_token = substring(md5(random()::text || id::text), 1, 8) where qr_token is null;
-- ;;
insert into cell_labels (unit_id, cell_row, cell_col, label)
select u.id, v.r, v.c, v.label
from (values (0,0,'Detroit & Chicago'), (0,1,'Acid')) as v(r, c, label)
join units u on u.owner_id='demo' and u.code='K1'
on conflict (unit_id, cell_row, cell_col) do nothing;
-- ;;
insert into gigs (owner_id, name, venue, gig_date, bag_unit_id, status)
select 'demo', v.name, v.venue, v.d::date, b.id, v.status
from (values ('Nowadays — Sunday','Nowadays','2026-08-30','returned'),
             ('Basement warm-up','Basement','2026-10-31','planning')) as v(name, venue, d, status)
join units b on b.owner_id='demo' and b.code='B1'
where not exists (select 1 from gigs g where g.owner_id='demo' and g.name=v.name);
-- ;;
-- Past gig: packed the day before, played, returned the day after.
insert into gig_items (gig_id, record_id, position, packed_at, played, returned_at)
select g.id, r.id, v.pos, '2026-08-29 18:00-04', true, '2026-08-31 14:00-04'
from (values ('Can You Feel It',1),('Energy Flash',2),('Acid Tracks',3),('Voodoo Ray',4)) as v(title, pos)
join gigs g on g.owner_id='demo' and g.name='Nowadays — Sunday'
join records r on r.owner_id='demo' and r.title=v.title
on conflict (gig_id, record_id) do nothing;
-- ;;
-- Upcoming gig: planned, nothing packed yet.
insert into gig_items (gig_id, record_id, position)
select g.id, r.id, v.pos
from (values ('Can You Feel It',1),('Pacific State',2),('Good Life',3),
             ('Higher State Of Consciousness',4),('Strings Of Life',5)) as v(title, pos)
join gigs g on g.owner_id='demo' and g.name='Basement warm-up'
join records r on r.owner_id='demo' and r.title=v.title
on conflict (gig_id, record_id) do nothing;
-- ;;
insert into plays (record_id, gig_id, played_at, venue)
select i.record_id, g.id, timestamptz '2026-08-30 23:00-04' + (i.position - 1) * interval '25 minutes', g.venue
from gig_items i join gigs g on g.id=i.gig_id and g.owner_id='demo' and g.name='Nowadays — Sunday'
where i.played
  and not exists (select 1 from plays p where p.record_id=i.record_id and p.gig_id=g.id);
-- ;;
-- An old play so "not played in a year" has something to show.
insert into plays (record_id, played_at, note)
select r.id, '2025-06-14 22:30-04', 'Rooftop set'
from records r
where r.owner_id='demo' and r.title='Strings Of Life'
  and not exists (select 1 from plays p where p.record_id=r.id and p.played_at='2025-06-14 22:30-04');
