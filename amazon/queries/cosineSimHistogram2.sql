select
round(count1.cnt*1.0/countAll.cnt, 3) as '0.0 - 0.1',
round(count2.cnt*1.0/countAll.cnt, 3) as '0.1 - 0.2',
round(count3.cnt*1.0/countAll.cnt, 3) as '0.2 - 0.3',
round(count4.cnt*1.0/countAll.cnt, 3) as '0.3 - 0.4',
round(count5.cnt*1.0/countAll.cnt, 3) as '0.4 - 0.5',
round(count6.cnt*1.0/countAll.cnt, 3) as '0.5 - 0.6',
round(count7.cnt*1.0/countAll.cnt, 3) as '0.6 - 0.7',
round(count8.cnt*1.0/countAll.cnt, 3) as '0.7 - 0.8',
round(count9.cnt*1.0/countAll.cnt, 3) as '0.8 - 0.9',
round(count10.cnt*1.0/countAll.cnt, 3) as '0.9 - 1.0'
from
(select count(*) as cnt from Similarities where NumUsers > 1) as countAll,
(select count(*) as cnt from Similarities where NumUsers > 1 and CosineSim <= 0.1) as count1,
(select count(*) as cnt from Similarities where NumUsers > 1 and CosineSim > 0.1 and CosineSim <= 0.2) as count2,
(select count(*) as cnt from Similarities where NumUsers > 1 and CosineSim > 0.2 and CosineSim <= 0.3) as count3,
(select count(*) as cnt from Similarities where NumUsers > 1 and CosineSim > 0.3 and CosineSim <= 0.4) as count4,
(select count(*) as cnt from Similarities where NumUsers > 1 and CosineSim > 0.4 and CosineSim <= 0.5) as count5,
(select count(*) as cnt from Similarities where NumUsers > 1 and CosineSim > 0.5 and CosineSim <= 0.6) as count6,
(select count(*) as cnt from Similarities where NumUsers > 1 and CosineSim > 0.6 and CosineSim <= 0.7) as count7,
(select count(*) as cnt from Similarities where NumUsers > 1 and CosineSim > 0.7 and CosineSim <= 0.8) as count8,
(select count(*) as cnt from Similarities where NumUsers > 1 and CosineSim > 0.8 and CosineSim <= 0.9) as count9,
(select count(*) as cnt from Similarities where NumUsers > 1 and CosineSim > 0.9 and CosineSim <= 1.0) as count10
;
