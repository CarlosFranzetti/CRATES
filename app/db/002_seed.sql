-- Crates: demo seed for owner 'demo' (idempotent; safe to re-run)
-- Statements are separated by a line containing only "-- ;;".

insert into units (owner_id, code, name, kind, preset_key, rows, cols, finish_name, finish_hex, sort) values
  ('demo','K1','Kallax 1','shelf','ikea-kallax-2x4',2,4,'White','#F2F0EB',0),
  ('demo','B1','Crater','bag','udg-ultimate-60',1,1,'Black','#1D1F22',1)
on conflict (owner_id, code) do nothing;
-- ;;
insert into records (owner_id, artist, title, label, year, country, format, genres, styles)
select 'demo', v.artist, v.title, v.label, v.year, v.country, '12"', array['Electronic'], v.styles
from (values
  ('Model 500','No UFO''s','Metroplex',1985,'US',array['Electro','Techno']),
  ('Rhythim Is Rhythim','Strings Of Life','Transmat',1987,'US',array['Detroit Techno']),
  ('Mr. Fingers','Can You Feel It','Trax Records',1986,'US',array['Deep House']),
  ('Joey Beltram','Energy Flash','R&S Records',1990,'Belgium',array['Techno']),
  ('Phuture','Acid Tracks','Trax Records',1987,'US',array['Acid House']),
  ('Josh Wink','Higher State Of Consciousness','Strictly Rhythm',1995,'US',array['Acid','Techno']),
  ('808 State','Pacific State','ZTT',1989,'UK',array['House','Acid House']),
  ('Inner City','Good Life','10 Records',1988,'UK',array['House']),
  ('A Guy Called Gerald','Voodoo Ray','Rham!',1988,'UK',array['Acid House']),
  ('Daft Punk','Around The World','Virgin',1997,'France',array['French House'])
) as v(artist, title, label, year, country, styles)
where not exists (select 1 from records r where r.owner_id='demo' and r.artist=v.artist and r.title=v.title);
-- ;;
-- Locations: (unit code, row, col) current; (home code, row, col) home. Row 0 = A, col 0 = 1.
insert into record_locations (record_id, unit_id, cell_row, cell_col, home_unit_id, home_row, home_col)
select r.id, u.id, v.cr, v.cc, h.id, v.hr, v.hc
from (values
  ('No UFO''s','K1',0,0,'K1',0,0),
  ('Strings Of Life','K1',0,0,'K1',0,0),
  ('Can You Feel It','K1',0,0,'K1',0,0),
  ('Energy Flash','K1',0,0,'K1',0,0),
  ('Acid Tracks','K1',0,0,'K1',0,0),
  ('Higher State Of Consciousness','K1',0,1,'K1',0,1),
  ('Pacific State','K1',0,1,'K1',0,1),
  ('Good Life','B1',0,0,'K1',0,1),
  ('Voodoo Ray','B1',0,0,'K1',0,0),
  ('Around The World','B1',0,0,'K1',0,1)
) as v(title, ucode, cr, cc, hcode, hr, hc)
join records r on r.owner_id='demo' and r.title=v.title
join units u on u.owner_id='demo' and u.code=v.ucode
join units h on h.owner_id='demo' and h.code=v.hcode
on conflict (record_id) do nothing;
-- ;;
insert into location_events (record_id, to_unit, to_row, to_col, reason)
select l.record_id, l.unit_id, l.cell_row, l.cell_col, 'add'
from record_locations l join records r on r.id=l.record_id and r.owner_id='demo'
where not exists (select 1 from location_events e where e.record_id=l.record_id);
-- ;;
insert into media_links (record_id, provider, external_id, rank, status)
select r.id, 'youtube', x.yt, (x.ord - 1)::smallint, 'pending'
from (values
  ('No UFO''s','UHja6QCvwRc,EarSRa19sZc,XtkpjkpD8xQ'),
  ('Strings Of Life','5oMUQKLzXH4,Hu3qPCAWgNg,jNREVOeGI5w'),
  ('Can You Feel It','AG040c9mkbg,1N9Wnqz8Rh8,Z1LAAenjlIw'),
  ('Energy Flash','AvqUnGKk7F8,maOM81a-Gyg,awdWUt7sI5I'),
  ('Acid Tracks','RbJTxipRrRY,QZSd2pP2dms,8P7w7waKT-0'),
  ('Higher State Of Consciousness','d3hAnAnJwyU,1Z9mhK8Liqg,Ldfc68bxlB8'),
  ('Pacific State','6jQ_bOP0HfY,Tv0UiQ5n7SM,rtUf9fDgtV0'),
  ('Good Life','M4_fMRNVvqA,EC40LAcZGkE,cPPRw5Ad86c'),
  ('Voodoo Ray','UwXSsNAtGTU,BEGRBp8-fvY'),
  ('Around The World','K0HSD_i2DvA,LKYPYj2XX80,T0lxekHV0qU')
) as v(title, ids)
join records r on r.owner_id='demo' and r.title=v.title
cross join lateral unnest(string_to_array(v.ids, ',')) with ordinality as x(yt, ord)
on conflict (record_id, provider, external_id) do nothing;
-- ;;
insert into playlists (owner_id, name, description, color, sort)
select 'demo','Warm-up','Deep, early-evening openers','#C8A2FF',0
where not exists (select 1 from playlists where owner_id='demo' and name='Warm-up');
-- ;;
insert into playlist_items (playlist_id, record_id, position)
select p.id, r.id, v.pos
from (values ('Can You Feel It',1),('Pacific State',2),('Voodoo Ray',3),('Good Life',4)) as v(title, pos)
join playlists p on p.owner_id='demo' and p.name='Warm-up'
join records r on r.owner_id='demo' and r.title=v.title
where not exists (select 1 from playlist_items i where i.playlist_id=p.id and i.record_id=r.id);
