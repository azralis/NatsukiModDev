#Aaa this code is so clean!!!!! I really need to learn how to write like this! -Daisy

label ch30_autoload:
    #Start with black scene
    scene black

    python:
        quick_menu = True
        style.say_dialogue = style.normal
        in_sayori_kill = None
        allow_skipping = True
        config.allow_skipping = False

    #Do all the things here for initial setup/flow hijacking
    python:
        # weather tracking is setup so we start it up
        if persistent.is_weather_tracking_set_up:
            weather.Weather.get_weather_detail.start()

    #FALL THROUGH

label ch30_holiday_check:
    #Run holiday checks and push/setup holiday related things here

    #FALL THROUGH

label ch30_visual_setup:
    $ main_background.draw(True)

    #FALL THROUGH

label ch30_init:

    # Add to the total visits counter
    $ persistent.jn_total_visit_count += 1

    #Let's pick a greeting
    $ push(greetings.select_greeting())

    # Reset the previous admission, now that Natsuki will have picked one if relevant
    $ persistent.jn_player_admission_type_on_quit = None

    $ main_background.draw(full_redraw=True)
    #show natsuki a zorder 3
    show Natsuki zorder 3
    show screen hkb_overlay(Action=False)
    #Do all var-sets, resets, and sanity checks prior to entering the loop here

    #And finally, we head into the loop
    jump ch30_loop


#The main loop
label ch30_loop:
    #Do topic selection here
    $ push(pick_random_topic(unlocked=True, player_says=False, location=main_background.location.id, affinity=20, trust=60))

    #Run our checks
    python:
        _now = datetime.datetime.now()
        if LAST_MINUTE_CHECK.minute != _now.minute:
            minute_check()
            LAST_MINUTE_CHECK = _now

        if LAST_HOUR_CHECK != _now.hour:
            hour_check()
            LAST_HOUR_CHECK = _now.hour

        if LAST_DAY_CHECK != _now.day:
            day_check()
            LAST_DAY_CHECK = _now.day

        coroutine_check()

        #We'll also check if we need to redraw the room
        #main_background.check_redraw()

    #Now, as long as there's something in the queue, we should go for it
    while persistent._event_list:
        call call_next_topic

    jump ch30_loop


label ch30_wait:
    window hide
    $ renpy.pause(delay=5.0, hard=True)
    jump ch30_loop


init python:
    LAST_MINUTE_CHECK = datetime.datetime.now()
    LAST_HOUR_CHECK = LAST_MINUTE_CHECK.hour
    LAST_DAY_CHECK = LAST_MINUTE_CHECK.day

    def minute_check():
        """
        Runs every minute during breaks between topics
        """
        if persistent.weather_validate_apikey_in_time is not None:
            if persistent.weather_validate_apikey_in_time <= datetime.datetime.now():
                persistent.weather_validate_apikey_in_time = None
                push('talk_weather_setup_part2')

    def hour_check():
        """
        Runs every hour during breaks between topics
        """

    def day_check():
        """
        Runs every day during breaks between topics
        """
        # everyday check if OWM apikey somehow wasn't invalidated
        if persistent.is_weather_tracking_set_up and not weather.is_api_key_valid():
            utils.log("API key for OpenWeatherMap is no longer valid", store.utils.SEVERITY_ERR)

    def coroutine_check():
        """
        Runs through all functions with @coroutine_loop and checks if they should be called
        """
        for func, info in store.utils.coroutine_loop.all.items():
            if info["next"] is None:
                continue

            if info["next"] <= datetime.datetime.now():
                func()

            if info["looping"]:
                store.utils.coroutine_loop.all[func]["next"] = info["loop_time"]+datetime.datetime.now()

#Other labels
label call_next_topic:
    if persistent._event_list:
        $ topic = persistent._event_list.pop(0)

        if renpy.has_label(topic):
            call expression topic

    python:
        #Collect our return keys here
        return_keys = _return if _return else dict()

        topic_obj = get_topic(topic)

        #Handle all things which act on topic objects here, since we can't access attributes of Nonetypes
        if topic_obj is not None:
            #Increment shown count
            topic_obj.shown_count += 1

            #Now manage return keys
            if "derandom" in return_keys:
                topic_obj.random = False

            if "lock" in return_keys:
                if topic_obj:
                    topic_obj.unlocked = False

    #This topic might quit
    if "quit" in return_keys:
        jump _quit

    return



label talk_menu:
    python:
        topics_ = get_all_topics(player_says=True, unlocked=True, location=main_background.location.id, affinity=20, trust=65)
        addit_topics = [
            ("Nevermind", "menu_nevermind"),
            ("Goodbye", farewells.select_farewell())
            ]
        menu_items = menu_list(topics_, addit_topics)
        choice = menu(menu_items)
        push(choice)
    jump ch30_loop

label dates_menu:
    python:
        topics_ = get_all_topics(player_says=True, unlocked=True, category=["date"])
        addit_topics = [("Nevermind", "menu_nevermind")]

        menu_items = menu_list(topics_, addit_topics)
        choice = menu(menu_items)
        push(choice)
    jump ch30_loop

label action_menu:
    python:
        topics_ = get_all_topics(player_says=True, unlocked=True, location=main_background.location)
        addit_topics = [("Nevermind", "menu_nevermind")]

        menu_items = menu_list(topics_, addit_topics)
        choice = menu(menu_items)
        push(choice)
    jump ch30_loop

label music_menu:
    menu:
        n "Want a change of tune?"
        "track1":
            play music track1
        "track2":
            play music track2
        "track3":
            play music track3
        "track4":
            play music track4
        "custom music":
            python:
                custom_tracks = get_custom_tracks()
                custom_tracks.append(("Nevermind", "menu_nevermind"))
                choice = menu(custom_tracks)
            if choice != "menu_nevermind":
                play music choice
            else:
                call expression choice
        "Nevermind":
            n "Okay!"

    jump ch30_loop

    jump ch30_loop

label extras_menu:
    python:
        topics_ = get_all_topics(player_says=True, unlocked=True, location=main_background.location)
        addit_topics = [("Nevermind", "menu_nevermind")]

        menu_items = menu_list(topics_, addit_topics)
        choice = menu(menu_items)
        push(choice)
    jump ch30_loop
