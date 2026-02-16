Scratchpad

### I'd like to improve the UX now that we have the basic functionality together. Right now the UX is quite messy. can you come up with a few ways to improve the UX theres a few areas i'd like to focus on but also open to your reccomendations

LOST CHANGES 

 can we rename single window to One Window and Full day to Multiple Windows?   

can you help me figure out a way to locally disable the password page, it's annoying to enter a password everytime im testing, maybe something we  
  can include in the .env file  

1) we should reasses the purpose of the side bar and what variables show up there, keep in mind for most cases dispatchers will just be bulk         
  uploading deliveries via csv, and they can now edit that information in the main window. Maybe we move those into the main window for modificaiton   
  there vs in side bar, also location should be automatically detected from the csv import    

❯ We need to make it cleared in what order things are supposed to happen, first you upload the file, then verify address, then pick optimization
  mode, then you hit optimize, I am thinking it makes more sense for these things to live in the side bar and show up as they get filled out.     
                                                                                                                                                    
  so first user has to upload file, then they verify the address and pick optimization mode, once an mode is selected, advanced config options are
  available and the option to run optimization is available, it being between two panes is confusing today we can either show this throw graying out   
  these items, or they appear after prior section is complete, use askuserquesiton tool to help me think through this     

❯ when i said allocation strategy, I meant the current allocation strategy which asks for priority customers, auto cancel threshold and auteo   
  reschedule threshold, not even, priority or capacity, this logic should be reverted to the prior  

❯ im checking the algorithim with a route that has less capacity in one window then the subsequent window, instead of the orders being moved into the
  next available window that makes sense, the orders were identified for reschedule, but not actually placed into that route, for each per window 
  optimization result, we should have KEEP (which is the original orders on that route), ADD (which are orders that have been moved into that route),  
  RESCHEDULE (which shoudl be orders that have been moved out of that route) and CANCEL (which should be orders that have been cancelled) help me 
  think through how to make sure this is easy to understand for dispatchers, use askuserquestion tool      

  ❯ since allocation strategy is being placed in the sidebar, we no longer need it in the main section under multi window, can you remove this please  
  and make sure the sidebar logic for cancel and reschedule thresholds is hooked up properly   

❯ we should move global allocation details under allocation summary, the orders moved early, reschsdule and cancel tables should be collapsed by     
  default but should have the number of orders with that action in brackets in the title. i.e. Orders Moved Early (1)      

final total on per window allocation breakdown should say En Route Totals as final total is confusing as the last column after cancel and reschdule in the same view    
  
the per window optimzation results tables are missing delivery early eligible information (this would have been shown in the initial import) can     
  you make sure this information (and anything else) is also visible in the per window optimization tables? 

❯ dont make it over complicated, just keep the column headers identical to the initial import, earlyEligible should be called earlyEligible use        
  askuserquestion tool  

❯ lets keep prior reschedule count in this table, can you also make sure the tables in global allocation details follow this?                  

❯ we can remove ✅ KEEP (On Route) for each table, that's no longer accurate as orders may be moving between windows, we should also add a new column
  that explains each order in the per-window optimization route table that has the order flow states, keep, recieved  

we do not need order movement details and orders moved between windows, can you remove order movement details header section and table as it is    
  already covered in orders moved between windows table?        

❯ 1) give the dispatcher in the sidebar the option to run additional cuts 2 and 3 only if they want to, 1 (the reccomeneded max orders option) should
  always be default selected. The dispatcher sandbox can be removed,                                                                                   
  use askuserquestion tool        

❯ i want to select the cuts i want to run in the sidebar before hitting run optimization like we do when we have to select the allocation strategy in
  the side bar for multiple windows      

❯ ok to be clear, the cuts that are being run in Cut 1, max orders, cut 2, shortest distance route, and cut 3 highest density route (prioritizting   
  delivereys per hour). this logic should not have been changed, can you make sure this is the case?   

❯ can you rename the optimization scenarios accordingly, penalty based and high penality is not friendly for dispatch, should be shortens and high   
  density      

❯ actually keep the vehicle capacity configuration in the side bar, maybe underneath the choose delivery window selector. revert back to the prior ux
  and the main page should not be editable  

4) We should clean up the debug messages across the entire UX, remove unecessary messages and improve the input heierachy, help me think through what could be improved here


For One Window Optimization, 


1) we should reasses the purpose of the side bar and what variables show up there, keep in mind for most cases dispatchers will just be bulk uploading deliveries via csv, and they can now edit that information in the main window. Maybe we move those into the main window for modificaiton there vs in side bar, also location should be automatically detected from the csv import

We need to make it cleared in what order things are supposed to happen, first you upload the file, then verify address, then pick optimization mode, then you hit optimize, I am thinking it makes more sense for these things to live in the side bar and show up as they get filled out. 
so first user has to upload file, then they verify the address and pick optimization mode, once an mode is selected, advanced config options are available and the option to run optimization is available, it being between two panes is confusing today

since allocation strategy is being placed in the sidebar, we no longer need it in the main section under multi window, can you remove this please and make sure the sidebar logic for cancel and reschedule thresholds is hooked up properly

1) give the dispatcher in the sidebar the option to run additional cuts 2 and 3 only if they want to, 1 (the reccomeneded max orders option) should always be default selected. The dispatcher sandbox can be removed,

2) make veihcle capacity editable in main window for one window optimization
3) remove early delivery table (and reschedule if present) and combine with do not delivery in this window (with action deliver early, or reschedule) similar to what we did in multi window one window optimization
4) make sure the table columns match the import i.e. earlyEligible vs early_delivery_ok.

3) I'm not seeing metrics for each of the windows like I do when i run single window when. I run multiple window I should be seeing Orders, Capacity Used, Route Time, Deliveres/Hour, Route Miles for each route, and there should also be global metrics like, Total Orders Delivered (across all routes), Capacity Used (across all routes), Total Route Time (across all routes), Deliveres/Hour (average across all routes), Route Miles (across all routes)


2) I want to consolidate the UX for the AI chat, and think we could move it into the sidebar, the AI results will be beside the output of the system and can be easily accessed, this should be the case for both single window and multi window optimizaitons, mutli window ai should be functioning very similar to the single window AI, can you help me think through this?

6) Remove random sample generator, comment this for now as we may want to use it in the future.
7) Update expected CSV format to the actual format, include a link to this exporter so dispatchers can export the data from the database directly if needed :https://metabase.prod.gobuncha.com/question/12227-buncher-exporter?date=2026-02-13&Delivery_window=&Fulfillment_Geo=


for the time being 


- Rename Reason to Assitant Reason and reorder in global allocation table to be right after numberOfUnits and before runId


v3 - have two modes for full day optimization, Post-Mortem, Live
- Post Mortem mode will allow operations to validate a days worth of dispatched orders, the goal here is to identify areas for improvement and provide suggestions on how the day could have been differently optimized
- Live mode will allow operations to in real time upload orders as they come in, dispatchers will make decisions based off of the orders that come in and the optimization output, this mode the model should act as if its helping the dispatcher move orders in real time. 


AI
- the AI should comletley and thorgohly understand and validate each route before submitting for user review, it should be able to justify decisions made. the ai should review each algorithic output and directly manipulate a final route if it thinks the algorithim is not fast enough, the AI during processing should show a log of thoughts it is having.



Completed:
can you make all tables in each route the full csv original import instead of the summary so we can see all teh attributes for each order

can you make optimization mode default full day
Priority customer lock disabled by default
All status on by default

can you make all tables in each per window optimzation show the full original import columns (like early to delivery eligible, prior reschedule count) instead of the summary so we can see all teh attributes for each order

can you make the orders, units uneditable but capacity configuration and window length by window an editable table for easier entry and modification and so it takes up less space in the ux if capacity is siffecient then just make the cell green, if not make cell red

make utilization bar green if there is enough capacity and red if it is over capacity 

generate a global summary map with stops linked together for each route/window, each route/window is a different color, the routes should be accurate

The map is not visible, nothing populates and the application automatically refreshes for some reason

make all order status on by default in configuration

allocation summary should only show if the allocation has not happened fully yet, make sure this shows up at the very end

testing - dont call actual maps 

Missing full table details in all tables, per window optimization tables do not have full table and neither does global allocation details

Lets consolidate AI Chats for single window and multiple windows into the sidebar moving forward. this will be the best place for it as then the dispatcher can use ask the AI questions while viewing the map.

in single window optimization, the tables show all the values, can you make sure in full day optimization this also is the case 

also rename one window to single window


we should put random sample generator, and test mode toggle also under advanced configutation
config default should be 3710 Dix Hwy Lincoln Park, MI 48146



Should have summary KPI's for each window optimized as well as global kpis for Total Miles, Deliveries per Hour, Dead Leg and Route Time for each 

Lets add cut 2 and 3 into cut four as options to prepopulate, cut 2 and 3 dont need to be run unless a dispatcher wants them to be on the cut four page and edit the route

Go from 8 to 6 and remove load factor % and instead of having keep orders and total orders, just have keep/total orders I would also keep Capacity Used, Delivers/Hour, Total Route Time and Keep/Total Orders. Dead Leg time, Route Miles displace in two rows of three metrics, can you also make sure these metrics show up in the multi window analysis?

we dont need to show fulfillment, default capcity in side bar as these can be configured if and when a dispatcher wants to run a single window optimization, also the fulfillment location should auto popoulate from the import, so I would remove that completley. Servie Time can stay and test mode toffle can stay




===
UX Fixes
- How can we simplify the UX, theres a lot of debugging stuff in here 
- We should move sidebar configuration into main area, we can probably remove capacity and location and window ovveride as we are taking that in via the main area with table input, are there other ways to make the UX cleaner? 

- use sidebar for uploading orders, filter by status, remove no ai option, remove random sample button 

-  Remove choice between full day and single window and just automate this, if an user uploads a csv, let them select which windows to optimize, default should be all selected and they can deselect multiple winodows if they want.
- the configuration side bar doesn't make a ton of sense now with there being a ton of congif in the main dashboard now
- generate a global summary map with stops linked together for each route/window, each route/window is a different color, the routes should be accurate based of the routes traveled by the van
- Mapbox API 

