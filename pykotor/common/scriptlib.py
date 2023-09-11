KOTOR_LIBRARY = {
    'k_inc_cheat': b'''//:: k_inc_cheat

/*

    This will be localized area for all

    Cheat Bot scripting.

*/

//:: Created By: Preston Watamaniuk

//:: Copyright (c) 2002 Bioware Corp.



#include "k_inc_debug"



//Takes a PLANET_ Constant

void CH_SetPlanetaryGlobal(int nPlanetConstant);

//Makes the specified party member available to the PC

void CH_SetPartyMemberAvailable(int nNPC);



//::///////////////////////////////////////////////

//:: Set Planet Local

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    VARIABLE = K_CURRENT_PLANET

        Endar Spire     5

        Taris           10

        Dantooine       15

        --Kashyyk       20

        --Manaan        25

        --Korriban      30

        --Tatooine      35

        Leviathan       40

        Unknown World   45

        Star Forge      50

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 16, 2002

//:://////////////////////////////////////////////



void CH_SetPlanetaryGlobal(int nPlanetConstant)

{

    if(nPlanetConstant == PLANET_ENDAR_SPIRE)

    {

        SetGlobalNumber("K_CURRENT_PLANET", 5);

    }

    else if(nPlanetConstant == PLANET_TARIS)

    {

        SetGlobalNumber("K_CURRENT_PLANET", 10);

    }

    else if(nPlanetConstant == PLANET_DANTOOINE)

    {

        SetGlobalNumber("K_CURRENT_PLANET", 15);

    }

    else if(nPlanetConstant == PLANET_KASHYYYK)

    {

        SetGlobalNumber("K_CURRENT_PLANET", 20);

    }

    else if(nPlanetConstant == PLANET_KORRIBAN)

    {

        SetGlobalNumber("K_CURRENT_PLANET", 30);

    }

    else if(nPlanetConstant == PLANET_MANAAN)

    {

        SetGlobalNumber("K_CURRENT_PLANET", 25);

    }

    else if(nPlanetConstant == PLANET_TATOOINE)

    {

        SetGlobalNumber("K_CURRENT_PLANET", 35);

    }

    else if(nPlanetConstant == PLANET_LEVIATHAN)

    {

        SetGlobalNumber("K_CURRENT_PLANET", 40);

    }

    else if(nPlanetConstant == PLANET_UNKNOWN_WORLD)

    {

        SetGlobalNumber("K_CURRENT_PLANET", 45);

    }

    else if(nPlanetConstant == PLANET_STAR_FORGE)

    {

        SetGlobalNumber("K_CURRENT_PLANET", 50);

    }

}



//::///////////////////////////////////////////////

//:: Make NPC Available

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Sets an NPC as available

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 16, 2002

//:://////////////////////////////////////////////



void CH_SetPartyMemberAvailable(int nNPC)

{

    if(nNPC == NPC_BASTILA)

    {

        AddAvailableNPCByTemplate(NPC_BASTILA, "p_bastilla");

    }

    else if(nNPC == NPC_CANDEROUS)

    {

        AddAvailableNPCByTemplate(NPC_CANDEROUS, "p_cand");

    }

    else if(nNPC == NPC_CARTH)

    {

        AddAvailableNPCByTemplate(NPC_CARTH, "p_carth");

    }

    else if(nNPC == NPC_HK_47)

    {

        AddAvailableNPCByTemplate(NPC_HK_47, "p_hk47");

    }

    else if(nNPC == NPC_JOLEE)

    {

        AddAvailableNPCByTemplate(NPC_JOLEE, "p_jolee");

    }

    else if(nNPC == NPC_JUHANI)

    {

        AddAvailableNPCByTemplate(NPC_JUHANI, "p_juhani");

    }

    else if(nNPC == NPC_MISSION)

    {

        AddAvailableNPCByTemplate(NPC_MISSION, "p_mission");

    }

    else if(nNPC == NPC_T3_M4)

    {

        AddAvailableNPCByTemplate(NPC_T3_M4, "p_t3m4");

    }

    else if(nNPC == NPC_ZAALBAR)

    {

        AddAvailableNPCByTemplate(NPC_ZAALBAR, "p_zaalbar");

    }

}







''',

    'k_inc_dan': b'''#include "k_inc_generic"

#include "k_inc_utility"

int ROMANCE_DONE = 4;

int JUHANI_RESCUED = 1;

int JEDI_TRAINING_DONE = 7;



int JEDI_PATH_GUARDIAN = 1;

int JEDI_PATH_SENTINEL = 2;

int JEDI_PATH_CONSULAR = 3;





int DROID_STARTED = 1;

int DROID_DESTROYED = 2;

int DROID_DECEIVED = 3;

int DROID_RETURNED = 4;

int DROID_HELPED = 5;

int DROID_FINISHED = 6;

string sBastilaTag = "bastila";

string sCarthTag = "carth";

string sCouncilTag = "dan13_WP_council";



string SABER_BLUE = "g_w_lghtsbr01";

string SABER_GREEN = "g_w_lghtsbr03";

string SABER_GOLD = "g_w_lghtsbr04";

string WANDERING_HOUND_TAG = "dan_wanderhound";

//places an instance of a character based on the tag/template

// **TAG MUST BE THE SAME AS TEMPLATE**

void PlaceNPC(string sTag, string sLocation = "");



//Get Carth's Object

object GetCarth();



//Gets Bastila's object

object GetBastila();



//gets the center of the council chamber

vector GetChamberCenter();



// creature move along a waypoint path. Not interuptable.

void PlotMove(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE);



// creature move along a waypoint path. Not interuptable. Destroys self at the end

void PlotLeave(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE);



// returns true is a trigger has not been fired yet

// intended for one shot triggers

int HasNeverTriggered();



//returns true if, on Korriban, the player has convinced Yuthura to come to Dantooine.

int YuthuraHasDefected();



//Sets the progression of the Elise plot on Dantooine

void SetElisePlot(int nValue);



// returns true if the player has started the Elise plot

int ElisePlotStarted();



// returns true if the player has agreed to help the droid after it has returned to elise

int GetDroidHelped();



// returns true if c369 has been spoken to

int GetEliseDroidMet();



//  the Elise plot has not started yet

int GetElisePlotNeverStared();



// returns true if Elise has gone to the Jedi compund

int GetEliseInCompound();



// returns true if the Elise plot is over

int GetElisePlotDone();





//returns true if Elise's droid was returned to her

int GetEliseDroidReturned();



// changes the PC to a new Jedi Class and gives them the required xperience to level Up

void TurnPlayerIntoJedi();



//checks for a color crystal in the players inventory and creates a saber of that color

object CreateFirstLightsaber();



//creates droids for the danm14ab cutscene

void StartDroid(string sLetter, int nNum);



//

void WraperShowLevelUpGUI();

//void main(){}



// returns number of the remaining wndering hounds on the level

int GetNumberOfWanderingKathHounds();



// spawns the number of Kath hounds. recursive

void SpawnWanderingKathHound(int nNumberOfHounds);



void PlaceNPC(string sTag, string sLocation = "")

{

    if(!GetIsObjectValid(GetObjectByTag(sTag)))

    {

        CreateObject(OBJECT_TYPE_CREATURE,sTag,GetLocation(GetObjectByTag("POST_" + sTag + sLocation)));

    }

}



object GetCarth()

{

    return GetObjectByTag(sCarthTag);

}



object GetBastila()

{

    return GetObjectByTag(sBastilaTag);

}



vector GetChamberCenter()

{

    return GetPosition(GetObjectByTag(sCouncilTag));

}



void PlotMove(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE)

{



    int nInc = 1;

    object oWP;

    int nIdx;

    if(nFirst > nLast)

    {

        nInc = -1;

    }

    for(nIdx = nFirst - nInc; abs(nLast - nIdx) > 0 && abs(nLast - nIdx) <= abs((nLast - nFirst) + 1); nIdx = nIdx + nInc)

    {

        oWP = GetObjectByTag(sWayPointTag + IntToString(nIdx + nInc));

        if(GetIsObjectValid(oWP))

        {

            ActionForceMoveToObject(oWP,nRun,3.0f,5.0f);

        }

    }

    ActionDoCommand(SetCommandable(TRUE));

    SetCommandable(FALSE);

}



void PlotLeave(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE)

{

    int nInc = 1;

    object oWP;

    int nIdx;

    object oSelf = OBJECT_SELF;

    if(nFirst > nLast)

    {

        nInc = -1;

    }

    for(nIdx = nFirst - nInc; abs(nLast - nIdx) > 0 && abs(nLast - nIdx) <= abs((nLast - nFirst) + 1); nIdx = nIdx + nInc)

    {

        oWP = GetObjectByTag(sWayPointTag + IntToString(nIdx + nInc));

        if(GetIsObjectValid(oWP))

        {

            ActionForceMoveToObject(oWP,nRun,3.0f,5.0f);

        }

    }

    ActionDoCommand(DestroyObject(OBJECT_SELF));

    SetCommandable(FALSE);

}



int HasNeverTriggered()

{

    int bReturn;

    if(UT_GetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_01) == FALSE)

    {

        bReturn = TRUE;

        UT_SetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_01,TRUE);

    }

    return bReturn;

}



int YuthuraHasDefected()

{

    return GetGlobalNumber("KOR_FINAL_TEST") == 7;

}



void SetElisePlot(int nValue)

{

    SetGlobalNumber("DAN_ELISE_PLOT",nValue);

}



int ElisePlotStarted()

{

    return GetGlobalNumber("DAN_ELISE_PLOT") == DROID_STARTED;

}



int GetDroidHelped()

{

    return GetGlobalNumber("DAN_ELISE_PLOT") == DROID_HELPED;

}



int GetEliseDroidMet()

{

    return GetGlobalNumber("DAN_ELISE_PLOT") > DROID_STARTED &&

           GetGlobalNumber("DAN_ELISE_PLOT") < DROID_FINISHED;

}



int GetElisePlotNeverStared()

{

    return GetGlobalNumber("DAN_ELISE_PLOT") == 0;

}



int GetEliseInCompound()

{

    return GetGlobalBoolean("DAN_ELISE_COMPOUND");

}



int GetElisePlotDone()

{

    return GetGlobalNumber("DAN_ELISE_PLOT") >= DROID_FINISHED;

}



int GetEliseDroidReturned()

{

    return GetGlobalNumber("DAN_ELISE_PLOT") == DROID_RETURNED ||

           GetGlobalNumber("DAN_ELISE_PLOT") == DROID_HELPED;

}



void TurnPlayerIntoJedi()

{

    object oPC = GetFirstPC();

/*    int nXP = GetXP(oPC);

   // AurPostString("Current XP: " + IntToString(nXP),5,5,5.0);



    int nLevel = GetHitDice(oPC);

   // AurPostString("Current Level: " + IntToString(nLevel),5,6,5.0);



    int nXPNeeded = 1000 * FloatToInt((IntToFloat(nLevel) / 2.0) * (IntToFloat(nLevel) + 1.0));

   // AurPostString("XP Needed" + IntToString(nXPNeeded),5,7,5.0);



    int nSaved = nXP - nXPNeeded;

   // AurPostString("Extra: " + IntToString(nSaved),5,8,5.0);

    if(nSaved > 0)

    {

        SetGlobalBoolean("DAN_EXTRA",TRUE);

        int nLow = nSaved & 0xff;

        AurPostString(IntToString(nLow),5,9,5.0);

        int nHigh = (nSaved >> 8) & 0xff;

        AurPostString(IntToString(nHigh),5,10,5.0);

       // if (nLow > 0)

       // {

           SetGlobalNumber("DAN_EXTRA_XP",nLow - 128);

       // }

      //  if (nHigh > 0)

        //{

            SetGlobalNumber("DAN_EXTRA_XP2",nHigh - 128);

       //}

    } */



    int nJediPath = GetGlobalNumber("DAN_PATH_STATE");

    if(nJediPath > 0)

    {

        if(nJediPath == JEDI_PATH_GUARDIAN)

        {

            AddMultiClass(CLASS_TYPE_JEDIGUARDIAN,oPC);

        }

        else if (nJediPath == JEDI_PATH_SENTINEL)

        {

            AddMultiClass(CLASS_TYPE_JEDISENTINEL,oPC);

        }

        else if (nJediPath == JEDI_PATH_CONSULAR)

        {

            AddMultiClass(CLASS_TYPE_JEDICONSULAR,oPC);

        }

      //  int nLevel = GetHitDice(oPC);

      //  int nXPNeeded = 1000 * (nLevel / 2) * (nLevel + 1);

      //  SetXP(oPC,nXPNeeded);

    }

    //ShowLevelUpGUI();

    CancelPostDialogCharacterSwitch();

    NoClicksFor(0.6);

    DelayCommand(0.5,WraperShowLevelUpGUI());

}



object CreateFirstLightsaber()

{

    object oPC = GetFirstPC();

    object oSaber;

    object oCrystal = GetItemPossessedBy(GetFirstPC(),"dan13_plotcrys");

    SetPlotFlag(oCrystal,FALSE);

    DestroyObject(oCrystal);

   /* if(GetIsObjectValid(oSaber))

    {

        AssignCommand(oPC,ActionEquipItem(oSaber,INVENTORY_SLOT_RIGHTWEAPON));

    }*/

    int nJediPath = GetGlobalNumber("DAN_PATH_STATE");

    if(nJediPath > 0)

    {

        if(nJediPath == JEDI_PATH_GUARDIAN)

        {

            oSaber = CreateItemOnObject(SABER_BLUE,oPC);

        }

        else if (nJediPath == JEDI_PATH_SENTINEL)

        {

            oSaber = CreateItemOnObject(SABER_GOLD,oPC);

        }

        else if (nJediPath == JEDI_PATH_CONSULAR)

        {

            oSaber = CreateItemOnObject(SABER_GREEN,oPC);

        }

    }

    if(GetIsObjectValid(oSaber))

    {

      // ExecuteScript("k_pdan_player03",oPC);

        DelayCommand(0.1,AssignCommand(oPC,ActionEquipItem(oSaber,INVENTORY_SLOT_RIGHTWEAPON)));

    }

    return oSaber;

}



void StartDroid(string sLetter, int nNum)

{

    string sBase = "danm14aa_WP_droid";

    string sStartTag = sBase + sLetter + "_01";

    string sEndTag = sBase + sLetter + "_0" + IntToString(nNum);

    location lStart = GetLocation(GetObjectByTag(sStartTag));

    location lEnd = GetLocation(GetObjectByTag(sEndTag));



    object oDroid = CreateObject(OBJECT_TYPE_CREATURE, "pdan_mwdroid",lStart);

    AssignCommand(oDroid,ActionWait(0.5));

    AssignCommand(oDroid,ActionMoveToLocation(lEnd));





/*    if(GetIsObjectValid(GetObjectByTag(sTag + sLetter + "_01")))

    {

        PrintString("Aidan--FoundDroidWP");

    }

    else

    {

        PrintString("Aidan--Can't Find DroidWP");

    }*/

   // object oDroid = CreateObject(OBJECT_TYPE_CREATURE, "pdan_mwdroid",GetLocation(GetObjectByTag(sTag + sLetter + "_01")));

  //  AssignCommand(oDroid,ActionMoveToObject(GetObjectByTag(sTag + sLetter + "_0" + IntToString(nNum))));

}



void WraperShowLevelUpGUI()

{

    int bAdd = GetGlobalBoolean("DAN_EXTRA");

    int nHigh =(GetGlobalNumber("DAN_EXTRA_XP2") + 128) << 8;

   // AurPostString(IntToString(nHigh),5,12,5.0);

    int nLow = GetGlobalNumber("DAN_EXTRA_XP") + 128;

   // AurPostString(IntToString(nLow),5,13,5.0);

    int nExtra = nHigh  | nLow;

   // AurPostString("Extra Saved: " + IntToString(nExtra),5,14,5.0);

    if(bAdd)

    {

       // AurPostString("Setting: " + IntToString(nExtra),5,15,5.0);

        GiveXPToCreature(GetFirstPC(),nExtra);

    }

    SetGlobalNumber("DAN_EXTRA_XP",0);

    SetGlobalNumber("DAN_EXTRA_XP2",0);

    ShowLevelUpGUI();

}



int GetNumberOfWanderingKathHounds()

{

    int nNumber;

   // int nNumber2;

    int nCount = GetStringLength(WANDERING_HOUND_TAG);

    object oHound = GetFirstObjectInArea();

    while(GetIsObjectValid(oHound))

    {

     //   AurPostString("Tag: " + GetTag(oHound),5,3,5.0);

        if(GetStringLeft(GetTag(oHound),nCount) == WANDERING_HOUND_TAG)

        {

            nNumber++;

        }

       // nNumber2++;

        oHound = GetNextObjectInArea();

       // AurPostString("Tag: " + GetTag(oHound),5,4,5.0);

    }

    //AurPostString("Number of Objects: " + IntToString(nNumber2),5,5,5.0);

   // AurPostString("Number of Objects: " + IntToString(nNumber),5,6,5.0);

    return nNumber;

}



void SpawnWanderingKathHound(int nNumberOfHounds)

{

    string sHound = WANDERING_HOUND_TAG + IntToString(nNumberOfHounds);

    location lSpawn = GetLocation(GetObjectByTag( "WP_" + sHound + "_01" ));

    CreateObject(OBJECT_TYPE_CREATURE,sHound,lSpawn);

    nNumberOfHounds--;

    if(nNumberOfHounds > 0)

    {

        SpawnWanderingKathHound(nNumberOfHounds);

    }



}

''',

    'k_inc_debug': b'''//::///////////////////////////////////////////////

//:: KOTOR Debug Include

//:: k_inc_debug

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This contains the functions for inserting

    debug information into the scripts.

    This include will use Db as its two letter

    function prefix.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: June 12, 2002

//:://////////////////////////////////////////////



//Inserts a print string into the log file for debugging purposes.

void Db_MyPrintString(string sString);

//Makes the object running the script say a speak string.

void Db_MySpeakString(string sString);

//Makes the nearest PC say a speakstring.

void Db_AssignPCDebugString(string sString);

//Basically, a wrapper for AurPostString

void Db_PostString(string sString = "",int x = 5,int y = 5,float fShow = 1.0);



//::///////////////////////////////////////////////

//:: Debug Print String

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Inserts a print string into the log file for

    debugging purposes.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: June 12, 2002

//:://////////////////////////////////////////////



void Db_MyPrintString(string sString)

{

    if(!ShipBuild())

    {

        PrintString(sString);

    }

}



//::///////////////////////////////////////////////

//:: Debug Speak String

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Makes the object running the script say a

    speak string.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: June 12, 2002

//:://////////////////////////////////////////////



void Db_MySpeakString(string sString)

{

    SpeakString(sString);

}



//::///////////////////////////////////////////////

//:: Assign PC Debug String

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Assigns the nearest PC a speakstring for debug

    purposes.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: June 12, 2002

//:://////////////////////////////////////////////



void Db_AssignPCDebugString(string sString)

{

    object oPC = GetNearestCreature(CREATURE_TYPE_PLAYER_CHAR, PLAYER_CHAR_IS_PC);

    if(GetIsObjectValid(oPC))

    {

        AssignCommand(oPC, SpeakString(sString));

    }

}



//::///////////////////////////////////////////////

//:: Db_PostString

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//Basically, a wrapper for AurPostString

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 15, 2002

//:://////////////////////////////////////////////

void Db_PostString(string sString = "",int x = 5,int y = 5,float fShow = 1.0)

{

    if(!ShipBuild())

    {

        AurPostString(sString,x,y,fShow);

    }

}



''',

    'k_inc_drop': b'''//::///////////////////////////////////////////////

//:: KOTOR Treasure drop Include

//:: k_inc_drop

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

// Contains the functions for handling creatures dropping random treasure

//Only human creatures not of the beast subrace willdrop treasure dependant

//on their hit dice

//:://////////////////////////////////////////////

//:: Created By: Aidan Scanlan On: 02/06/03

//:://////////////////////////////////////////////



int DR_HIGH_LEVEL = 15;

int DR_MEDIUM_LEVEL = 10;

int DR_LOW_LEVEL = 5;

int DR_SUBRACE_BEAST = 2;

//Checks for treasure drop conditions. Returns True if treasure will drop

int DR_SpawnCreatureTreasure(object oTarget = OBJECT_SELF);

//Dependant on the level of a creature drops treasure from a list

void DR_CreateRandomTreasure(object oTarget = OBJECT_SELF);

// creates a low level treasure: med pack/repair, frag grenade, credits

void DR_CreateLowTreasure();

// creates midlevel treasure: adv-med/repair, any gredade, stims, credits

void DR_CreateMidTreasure();

// creates high treasure: adv stims, grenades, ultra med/repair, credits

void DR_CreateHighTreasure();

// Creates 1-4 credits

void DR_CreateFillerCredits();

/////////////////////////////////////////////////////////////////////////





//Checks for treasure drop conditions. Returns True if treasure will drop

int DR_SpawnCreatureTreasure(object oTarget = OBJECT_SELF)

{

    int nRace = GetRacialType(oTarget);

    int nFaction = GetStandardFaction(oTarget);

    int nSubRace = GetSubRace(oTarget);

    if(Random(4) == 0 &&

       nRace != RACIAL_TYPE_DROID &&

       nSubRace != DR_SUBRACE_BEAST)

    {

        //AurPostString("will drop",5,5,5.0);

        DR_CreateRandomTreasure(oTarget);

        return TRUE;

    }

    return FALSE;

}



//Dependant on the level of a creature drops treasure from a list

void DR_CreateRandomTreasure(object oTarget = OBJECT_SELF)

{

    int nLevel = GetHitDice(oTarget);

    if (nLevel > DR_HIGH_LEVEL)

    {

        DR_CreateHighTreasure();

        if(Random(2) == 0)

        {

            DR_CreateHighTreasure();

        }

        if(Random(2) == 0)

        {

            DR_CreateMidTreasure();

        }

    }

    else if (nLevel <= DR_HIGH_LEVEL && nLevel > DR_MEDIUM_LEVEL)

    {

        DR_CreateMidTreasure();

        if(Random(3) == 0)

        {

            DR_CreateHighTreasure();

        }

        if(Random(2) == 0)

        {

            DR_CreateMidTreasure();

        }

    }

    else if (nLevel <= DR_MEDIUM_LEVEL && nLevel > DR_LOW_LEVEL)

    {

        DR_CreateMidTreasure();

        if(Random(2) == 0)

        {

            DR_CreateLowTreasure();

        }

    }

    else

    {

        DR_CreateLowTreasure();

        if(Random(3) == 0)

        {

            DR_CreateLowTreasure();

        }

        if(Random(4) == 0)

        {

            DR_CreateMidTreasure();

        }

    }

}



// creates a low level treasure: med pack/repair, frag grenade, credits

void DR_CreateLowTreasure()

{

   //AurPostString("dropping low",5,6,5.0);

    string sTemplate;

    int nStack = 1;

    int nRandom = Random(6);

    switch(nRandom)

    {

        case 0: sTemplate = "g_i_drdrepeqp001";  //repair kit

        break;



        case 1:

            sTemplate = "g_i_credits001";// 5 stack

            nStack = 5;

            DR_CreateFillerCredits();

        break;



        case 2:

            sTemplate = "g_i_credits002";  //10 stack

            nStack = 10;

            DR_CreateFillerCredits();

        break;



        case 3:

            sTemplate = "g_i_credits003";  // 25 stack

            nStack = 25;

            DR_CreateFillerCredits();

        break;



        case 4: sTemplate = "g_i_medeqpmnt01";// med kit

        break;



        case 5: sTemplate = "g_w_fraggren01"; // frag grenade

        break;

    }



    CreateItemOnObject(sTemplate,OBJECT_SELF,nStack);

}



// creates midlevel treasure: adv-med/repair, any gredade, stims, credits

void DR_CreateMidTreasure()

{

    string sTemplate;

    int nStack = 1;

    int nRandom = Random(15);

    switch (nRandom)

    {

        case 0: sTemplate = "g_i_drdrepeqp002";  //advanced repair kit

        break;



        case 1:

            sTemplate = "g_i_credits004";  // 50 stack

            nStack = 50;

            DR_CreateFillerCredits();

        break;



        case 2: sTemplate = "g_i_medeqpmnt02"; //advanced med pack

        break;



        case 3: sTemplate = "g_i_cmbtshot001"; //battle stimulant

        break;



        case 4: sTemplate = "g_i_adrnaline003";  //adrenal stamina

        break;



        case 5: sTemplate = "g_i_adrnaline002"; // adrenal alacrity

        break;



        case 6: sTemplate = "g_i_adrnaline001"; // adrenal strength

        break;



        case 7:

            sTemplate = "g_w_stungren01";  // stun grenade

            nStack = 2;

        break;



        case 8:

            sTemplate = "g_w_fraggren01";  // fragmentation grenade

            nStack = 2;

        break;



        case 9: sTemplate = "g_w_poisngren01"; // poison gredade

        break;



        case 10: sTemplate = "g_w_sonicgren01"; // sonic grenade

        break;



        case 11: sTemplate = "g_w_adhsvgren001"; // adhesive grenade

        break;



        case 12: sTemplate = "g_w_cryobgren001";// cryo grenade

        break;



        case 13: sTemplate = "g_w_iongren01";// ion grenade

        break;

    }

    CreateItemOnObject(sTemplate,OBJECT_SELF,nStack);

}



// creates high treasure: adv stims, grenades, ultra med/repair, credits

void DR_CreateHighTreasure()

{

    string sTemplate;

    int nStack = 1;

    int nRandom = Random(16);

    switch (nRandom)

    {

        case 0: sTemplate = "g_i_drdrepeqp003";  //super repair kit

        break;



        case 1: sTemplate = "g_w_thermldet01"; //Thermal detinator

        break;



        case 2: sTemplate = "g_i_medeqpmnt03"; //life pack

        break;



        case 3: sTemplate = "g_i_cmbtshot003";//speed stim

        break;



        case 4: sTemplate = "g_i_cmbtshot002"; //hyper battle stim

        break;



        case 5: sTemplate = "g_i_adrnaline006"; //huper adrenal stamina

        break;



        case 6: sTemplate = "g_i_adrnaline005"; //hyper adrenal alacrity

        break;



        case 7: sTemplate = "g_i_adrnaline004";// hyper adrenal strength

        break;



        case 8:

        sTemplate = "g_w_poisngren01"; // poison gredade

        nStack = 2;

        break;



        case 9:

        sTemplate = "g_w_sonicgren01"; // sonic grenade

        nStack = 2;

        break;



        case 10:

        sTemplate = "g_w_adhsvgren001"; // adhesive grenade

        nStack = 2;

        break;



        case 11:

        sTemplate = "g_w_cryobgren001";// cryo grenade

        nStack = 2;

        break;



        case 12:

        sTemplate = "g_w_firegren001";// plasma grenade

        nStack = 2;

        break;



        case 13:

        sTemplate = "g_w_iongren01";// ion grenade

        nStack = 2;

        break;



        case 14:

        sTemplate = "g_i_credits015";

        nStack = Random(50) + 50;

        break;



        case 15: sTemplate = "g_w_firegren001";// plasma grenade

        break;



    }

    CreateItemOnObject(sTemplate,OBJECT_SELF,nStack);

}



// Creates 1-4 credits

void DR_CreateFillerCredits()

{

    CreateItemOnObject("g_i_credits015",OBJECT_SELF,Random(4) + 1);

}

''',

    'k_inc_ebonhawk': b'''//:: k_inc_ebonhawk

/*

     Ebon Hawk include file

*/

//:: Created By: Preston Watamaniuk

//:: Copyright (c) 2002 Bioware Corp.



//This checks the Star Map plot to see if it is at state 30.

int EBO_CheckStarMapPlot();

//Bastila intiates conversation with the PC

void EBO_BastilaStartConversation2();

//Should Bastila intiates conversation with the PC

int EBO_ShouldBastilaStartConversation();

//Bastila intiates conversation with the PC

void EBO_BastilaStartConversation2();

//Advances the state of the bounty hunters plot after galaxy map selections are made

void EBO_PlayBountyHunterCutScene();

//Play the current cutscene for taking off from the planet.

void EBO_PlayTakeOff(int nCurrentPlanet);

//Play the corrent cutscene for landing on the planet.

void EBO_PlayLanding(int nDestination);

//Creates items on the PC based on the NPC they are talking to.

void EBO_CreateEquipmentOnPC();

//Checks if the PC needs equipment based on the NPC they are talking to.

int EBO_GetIsEquipmentNeeded();

//Determines the number items held with specific tags

int EBO_CheckInventoryNumbers(string sTag1, string sTag2 = "", string sTag3 = "", string sTag4 = "");

//Returns the scripting constant for the current planet.

int EBO_GetCurrentPlanet();

//Returns the scripting constant for the future planet.

int EBO_GetFuturePlanet();

//Returns the correct K_CURRENT_PLANET value when a Planetary.2DA index is passed in.

int EBO_GetPlanetFrom2DA(int nPlanetIndex);

//Starts the correct sequence based on the planet being traveled to.

void EBO_PlayRenderSequence();



//::///////////////////////////////////////////////

//:: Check Star Map

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    If the variable K_STAR_MAP is at 30 and

    the variable K_CAPTURED_LEV = 5 then

    run the leviathan module.

    K_CAPTURED_LEV States

    0 = Pre Leviathan

    5 = Captured

    10 = Escaped

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 3, 2002

//:://////////////////////////////////////////////



int EBO_CheckStarMapPlot()

{

    int nStarMap = GetGlobalNumber("K_STAR_MAP");

    int nLev = GetGlobalBoolean("K_CAPTURED_LEV");

    if(nStarMap >= 40 && nLev == 5)

    {

        SetGlobalNumber("K_CURRENT_PLANET", 40);

        //This will be removed when the new galaxy map is rolled out.

        StartNewModule("ebo_m40aa");



        return TRUE;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Bastila Start Vision Conversation

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This function gets bastila to start the

    appropriate cutscene dialogue with the PC

    You can use k_vis_[PLANET] == FALSE to see

    if they have been their before and seen the

    planet vision. This applies to Dantooine,

    Manaan, Korriban, Tatooine and Kashyyyk.



    Also set the script so that if Ebon_Vision !=99

    then it fires the dialog file ebo_bast_vision

    and has Bastila init dialog on the Ebon Hawk.

    (If Ebon_Vision==99 the dialog will not fire,

    but it should still play the vision.

    15 to 35

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 3, 2002

//:://////////////////////////////////////////////



void EBO_BastilaStartConversation()

{

    int nPlanet = GetGlobalNumber("K_CURRENT_PLANET");

    int nVision = GetGlobalNumber("Ebon_Vision");

    int nFLAG = FALSE;

    if( (nPlanet == 15 || nPlanet == 20 || nPlanet == 25 || nPlanet == 30 || nPlanet == 35) && nVision != 99)

    {

        object oBast = GetNearestObjectByTag("Bastila");

        if(GetIsObjectValid(oBast))

        {

            if(nPlanet == 15 && !GetGlobalBoolean("k_vis_dantooine"))

            {

                nFLAG = TRUE;

                SetGlobalBoolean("k_vis_dantooine",1);

            }

            else if(nPlanet == 20 && !GetGlobalBoolean("k_vis_kashyyyk"))

            {

                nFLAG = TRUE;

                SetGlobalBoolean("k_vis_kashyyyk",1);

            }

            else if(nPlanet == 25 && !GetGlobalBoolean("k_vis_manaan"))

            {

                nFLAG = TRUE;

                SetGlobalBoolean("k_vis_manaan",1);

            }

            else if(nPlanet == 30 && !GetGlobalBoolean("k_vis_korriban"))

            {

                nFLAG = TRUE;

                SetGlobalBoolean("k_vis_korriban",1);

            }

            else if(nPlanet == 35 && !GetGlobalBoolean("k_vis_tatooine"))

            {

                nFLAG = TRUE;

                SetGlobalBoolean("k_vis_tatooine",1);

            }

            if(nFLAG == TRUE)

            {

                //HoldWorldFadeInForDialog();

                object oPC = GetFirstPC();

                AurPostString("I am going to talk", 5, 6, 4.0);

                AurPostString("Bastila is Valid = " + IntToString(GetIsObjectValid(oBast)), 5,7,4.0);

                AurPostString("PC is Valid = " + IntToString(GetIsObjectValid(oPC)), 5,8,4.0);

                AssignCommand(oBast, ActionStartConversation(oPC, "ebo_bast_vision", FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE));

            }

        }

    }

}



//::///////////////////////////////////////////////

//::Calo Nord / Bandon Variable Advancement

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This plot involves the PC being tracked across the galaxy.

    Plot is tracked with the K_KALO_BANDON variable

    1 - Leaving Dantooine --> Cutscene with Calo Nord = 0, set to 10.

    2 - On 3rd Star Map Planet --> Next villain encounter will spawn Nord = 10, set to 20

    3 - Leaving 3rd Starmap Planet --> Darth Bandon cutscene = 20, set to 30.

    4 - On 4th Star Map planet --> Darth Bandon Attacks = 30, set to 99

    Trigger have been placed on all the creamy middle planets to simulate

    the ambush

    10 - 1st Map Activated - Set K_KALO_BANDON to 10

    30 - 3rd Map Activated - Set K_KALO_BANDON to 30

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 9, 2002

//:://////////////////////////////////////////////

void EBO_PlayBountyHunterCutScene()

{

    int nStar = GetGlobalNumber("K_STAR_MAP");

    if(nStar == 10)

    {

        //NOTE - PLAY FIRST CUTSCENE WITH CALO NORD HERE

        SetGlobalNumber("K_KALO_BANDON", 10);

    }

    else if(nStar == 30)

    {

        //NOTE - PLAY SECOND CUTSCENE WITH DARTH BANDON HERE

        SetGlobalNumber("K_KALO_BANDON", 30);

    }

}



//::///////////////////////////////////////////////

//::Play Appropriate Travel Cutscenes

//::Calo Nord / Bandon Variable Advancement

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    K_STAR_MAP variable

    0 - No maps activated

    10 - 1st Map Activated

    20 - 2nd Map Activated

    30 - 3rd Map Activated

    40 - 4th Map Activated

    50 - 5th Map Activated



World Variables

    Global Number Variable: Planet Settings

    VARIABLE = K_CURRENT_PLANET

        Endar Spire     5

        Taris           10

        Dantooine       15

        --Kashyyk       20

        --Manaan        25

        --Korriban      30

        --Tatooine      35

        Leviathan       40

        Unknown World   45

        Star Forge      50

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 9, 2002

//:://////////////////////////////////////////////

string EBO_PlayTakeOff(int nCurrentPlanet)

{

    int nPlanet = nCurrentPlanet;//GetGlobalNumber("K_CURRENT_PLANET");

    if(nPlanet == 15)

    {

        PlayMovie("05_2c");

    }

    else if(nPlanet == 20)

    {

        PlayMovie("05_4c");

    }

    else if(nPlanet == 25)

    {

        PlayMovie("05_5c");

    }

    else if(nPlanet == 30)

    {

        PlayMovie("05_7c");

    }

    else if(nPlanet == 35)

    {

        PlayMovie("05_3c");

    }

    else if(nPlanet == 40)

    {

        //PlayMovie("");

    }

    else if(nPlanet == 45)

    {

        PlayMovie("05_8c");

    }

    return "NULL";

}



string EBO_PlayLanding(int nDestination)

{

    int nPlanet = GetGlobalNumber("K_CURRENT_PLANET");

    if(nPlanet == 15)

    {

        PlayMovie("05_2a");

    }

    else if(nPlanet == 20)

    {

        PlayMovie("05_4a");

    }

    else if(nPlanet == 25)

    {

        PlayMovie("05_5a");

    }

    else if(nPlanet == 30)

    {

        PlayMovie("05_7a");

    }

    else if(nPlanet == 35)

    {

        PlayMovie("05_3a");

    }

    else if(nPlanet == 40)

    {

        //PlayMovie("");

    }

    else if(nPlanet == 45)

    {

        PlayMovie("05_8a");

    }

    return "NULL";

}



//::///////////////////////////////////////////////

//:: Does the PC need equipment

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks the PCs inventory and determines based

    on OBJECT_SELF whether the PC needs equipment

    Returns true if the PC has enough of the selected

    item.



    The number of items given out is now tracked as

    of Feb 25, 2003.  The NPCs will not give out

    more items than the current setting of the

    star map variable + 5.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 19, 2002

//:://////////////////////////////////////////////

int EBO_GetIsEquipmentNeeded()

{

    int nNumber, nGlobal;

    string sTag = GetTag(OBJECT_SELF);

    int nStarMap = (GetGlobalNumber("K_STAR_MAP")*2) + 10;

    if(sTag == "zaalbar")

    {

        nNumber = EBO_CheckInventoryNumbers("G_w_StunGren01","g_w_iongren01","g_w_adhsvgren001");

        nGlobal = GetGlobalNumber("K_ZAALBAR_ITEMS");

        if((nNumber <= 10 && nGlobal < nStarMap) || nGlobal == 0)

        {

            return FALSE;

        }

        return TRUE;

    }

    else if(sTag == "jolee")

    {

        nNumber = EBO_CheckInventoryNumbers("g_I_medeqpmnt01","G_I_MEDEQPMNT02","g_I_medeqpmnt03");

        nGlobal = GetGlobalNumber("K_JOLEE_ITEMS");

        if((nNumber <= 10 && nGlobal < nStarMap) || nGlobal == 0)

        {

            return FALSE;

        }

        return TRUE;

    }

    else if(sTag == "mission")

    {

        nNumber = EBO_CheckInventoryNumbers("g_i_secspike01","G_I_SECSPIKE02");

        nGlobal = GetGlobalNumber("K_MISSION_ITEMS");

        if((nNumber <= 10 && nGlobal <= nStarMap) || nGlobal == 0)

        {

            return FALSE;

        }

        return TRUE;

    }

    else if(sTag == "cand")

    {

        nNumber = EBO_CheckInventoryNumbers("g_i_adrnaline001","G_I_ADRNALINE002","g_i_adrnaline003", "g_i_cmbtshot001");

        nGlobal = GetGlobalNumber("K_CAND_ITEMS");



        PrintString("Number = " + IntToString(nNumber));

        PrintString("Global = " + IntToString(nGlobal));

        PrintString("StarMap = " + IntToString(nStarMap));



        if((nNumber <= 10 && nGlobal <= nStarMap) || nGlobal == 0)

        {

            return FALSE;

        }

        return TRUE;

    }

    else if(sTag == "t3m4")

    {

        nNumber = EBO_CheckInventoryNumbers("K_COMPUTER_SPIKE");

        nGlobal = GetGlobalNumber("K_T3M4_ITEMS");



        if((nNumber <= 10 && nGlobal <= nStarMap) || nGlobal == 0)

        {

            return FALSE;

        }

        return TRUE;

    }

    return TRUE;

}



//::///////////////////////////////////////////////

//:: NPC Item Creation

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Determines who the person being talked to is

    and what items the character should receive.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 19, 2002

//:://////////////////////////////////////////////



void EBO_CreateEquipmentOnPC()

{

    int nCount;

    string sTag = GetTag(OBJECT_SELF);

    object oProxy;

    if(sTag == "zaalbar")

    {

        int nRand = d3();

        if(nRand == 1)

        {

            oProxy = CreateItemOnObject("g_w_stungren01", GetFirstPC());

        }

        else if(nRand == 2)

        {

            oProxy = CreateItemOnObject("g_w_iongren01", GetFirstPC());

        }

        else if(nRand == 3)

        {

            oProxy = CreateItemOnObject("g_w_adhsvgren001", GetFirstPC());

        }

        nCount = GetGlobalNumber("K_ZAALBAR_ITEMS");

        nCount++;

        SetGlobalNumber("K_ZAALBAR_ITEMS", nCount);

    }

    else if(sTag == "jolee")

    {

        int nLevel = GetHitDice(GetFirstPC());

        if(nLevel <= 4)

        {

            oProxy = CreateItemOnObject("G_I_MEDEQPMNT01", GetFirstPC());

        }

        else if(nLevel > 4 && nLevel <= 10)

        {

            oProxy = CreateItemOnObject("G_I_MEDEQPMNT02", GetFirstPC());

        }

        else if(nLevel > 10)

        {

            oProxy = CreateItemOnObject("G_I_MEDEQPMNT03", GetFirstPC());

        }

        nCount = GetGlobalNumber("K_JOLEE_ITEMS");

        nCount++;

        SetGlobalNumber("K_JOLEE_ITEMS", nCount);

    }

    else if(sTag == "mission")

    {

        int nLevel = GetHitDice(GetFirstPC());

        if(nLevel <= 7)

        {

            oProxy = CreateItemOnObject("g_i_secspike01", GetFirstPC());

        }

        else if(nLevel > 7)

        {

            oProxy = CreateItemOnObject("g_i_secspike02", GetFirstPC());

        }

        nCount = GetGlobalNumber("K_MISSION_ITEMS");

        nCount++;

        SetGlobalNumber("K_MISSION_ITEMS", nCount);

    }

    else if(sTag == "cand")

    {

        int nRand = d4();



        if(nRand == 1)

        {

            oProxy = CreateItemOnObject("G_I_ADRNALINE001", GetFirstPC());

        }

        else if(nRand == 2)

        {

            oProxy = CreateItemOnObject("G_I_ADRNALINE002", GetFirstPC());

        }

        else if(nRand == 3)

        {

            oProxy = CreateItemOnObject("G_I_ADRNALINE003", GetFirstPC());

        }

        else if(nRand == 4)

        {

            oProxy = CreateItemOnObject("G_I_CMBTSHOT001", GetFirstPC());

        }

        nCount = GetGlobalNumber("K_CAND_ITEMS");

        nCount++;

        SetGlobalNumber("K_CAND_ITEMS", nCount);

    }

    else if(sTag == "t3m4")

    {

        oProxy = CreateItemOnObject("G_I_PROGSPIKE01", GetFirstPC());

        nCount = GetGlobalNumber("K_T3M4_ITEMS");

        nCount++;

        SetGlobalNumber("K_T3M4_ITEMS", nCount);

    }

}



//::///////////////////////////////////////////////

//:: Count Inventory Items

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Counts and totals up to four different items

    within the PCs inventory.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 19, 2002

//:://////////////////////////////////////////////



int EBO_CheckInventoryNumbers(string sTag1, string sTag2 = "", string sTag3 = "", string sTag4 = "")

{

    int nNumber;

    object oGrenade;

    if(sTag1 != "")

    {

        oGrenade = GetItemPossessedBy(GetFirstPC(), sTag1);

        if(GetIsObjectValid(oGrenade))

        {

            nNumber += GetNumStackedItems(oGrenade);

        }

    }

    if(sTag2 != "")

    {

        oGrenade = GetItemPossessedBy(GetFirstPC(), sTag2);

        if(GetIsObjectValid(oGrenade))

        {

            nNumber += GetNumStackedItems(oGrenade);

        }

    }

    if(sTag3 != "")

    {

        oGrenade = GetItemPossessedBy(GetFirstPC(), sTag3);

        if(GetIsObjectValid(oGrenade))

        {

            nNumber += GetNumStackedItems(oGrenade);

        }

    }

    if(sTag4 != "")

    {

        oGrenade = GetItemPossessedBy(GetFirstPC(), sTag4);

        if(GetIsObjectValid(oGrenade))

        {

            nNumber += GetNumStackedItems(oGrenade);

        }

    }

    return nNumber;

}



//::///////////////////////////////////////////////

//:: Get Planet Constant

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Uses K_CURRENT_PLANET to return the current

    planets scripting constant

    0    Endar Spire     5

    1    Taris           10

    2    Dantooine       15

    3    --Kashyyk       20

    4    --Manaan        25

    5    --Korriban      30

    6    --Tatooine      35

    7    Leviathan       40

    8    Unknown World   45

    9    Star Forge      50

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 1, 2002

//:://////////////////////////////////////////////

int EBO_GetCurrentPlanet()

{

    int nPlanet = GetGlobalNumber("K_CURRENT_PLANET");

    if(nPlanet == 5)

    {

        return PLANET_ENDAR_SPIRE;

    }

    else if(nPlanet == 10)

    {

        return PLANET_TARIS;

    }

    else if(nPlanet == 15)

    {

        return PLANET_DANTOOINE;

    }

    else if(nPlanet == 20)

    {

        return PLANET_KASHYYYK;

    }

    else if(nPlanet == 25)

    {

        return PLANET_MANAAN;

    }

    else if(nPlanet == 30)

    {

        return PLANET_KORRIBAN;

    }

    else if(nPlanet == 35)

    {

        return PLANET_TATOOINE;

    }

    else if(nPlanet == 40)

    {

        return PLANET_LEVIATHAN;

    }

    else if(nPlanet == 45)

    {

        return PLANET_UNKNOWN_WORLD;

    }

    else if(nPlanet == 50)

    {

        return PLANET_STAR_FORGE;

    }

    return -1;

}



//::///////////////////////////////////////////////

//:: Get Planet Constant

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Uses K_FUTURE_PLANET to return the current

    planets scripting constant

    0    Endar Spire     5

    1    Taris           10

    2    Dantooine       15

    3    --Kashyyk       20

    4    --Manaan        25

    5    --Korriban      30

    6    --Tatooine      35

    7    Leviathan       40

    8    Unknown World   45

    9    Star Forge      50

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 1, 2002

//:://////////////////////////////////////////////

int EBO_GetFuturePlanet()

{

    int nPlanet = GetGlobalNumber("K_FUTURE_PLANET");

    if(nPlanet == 5)

    {

        return PLANET_ENDAR_SPIRE;

    }

    else if(nPlanet == 10)

    {

        return PLANET_TARIS;

    }

    else if(nPlanet == 15)

    {

        return PLANET_DANTOOINE;

    }

    else if(nPlanet == 20)

    {

        return PLANET_KASHYYYK;

    }

    else if(nPlanet == 25)

    {

        return PLANET_MANAAN;

    }

    else if(nPlanet == 30)

    {

        return PLANET_KORRIBAN;

    }

    else if(nPlanet == 35)

    {

        return PLANET_TATOOINE;

    }

    else if(nPlanet == 40)

    {

        return PLANET_LEVIATHAN;

    }

    else if(nPlanet == 45)

    {

        return PLANET_UNKNOWN_WORLD;

    }

    else if(nPlanet == 50)

    {

        return PLANET_STAR_FORGE;

    }

    else if(nPlanet == 55)

    {

        return PLANET_LIVE_01;

    }

    else if(nPlanet == 60)

    {

        return PLANET_LIVE_02;

    }

    else if(nPlanet == 65)

    {

        return PLANET_LIVE_03;

    }

    else if(nPlanet == 70)

    {

        return PLANET_LIVE_04;

    }

    else if(nPlanet == 75)

    {

        return PLANET_LIVE_05;

    }

    return -1;

}





int EBO_GetPlanetFrom2DA(int nPlanetIndex)

{

/*Scripting Constants              2DA Values

int PLANET_ENDAR_SPIRE      = 0;   0          Endar_Spire

int PLANET_TARIS            = 1;   1          Taris

int PLANET_EBON_HAWK        = 2;   2          Ebon_Hawk

int PLANET_DANTOOINE        = 3;   3          Dantooine

int PLANET_TATOOINE         = 4;   4          Tatooine

int PLANET_KASHYYYK         = 5;   5          Kashyyyk

int PLANET_MANAAN           = 6;   6          Manaan

int PLANET_KORRIBAN         = 7;   7          Korriban

int PLANET_LEVIATHAN        = 8;   8          Leviathan

int PLANET_UNKNOWN_WORLD    = 9;   9          Unknown_World

int PLANET_STAR_FORGE       = 10;  10         Star_Forge



Plot Values

0    Endar Spire     5

1    Taris           10

3    Dantooine       15

5    --Kashyyk       20

6    --Manaan        25

7    --Korriban      30

4    --Tatooine      35

8    Leviathan       40

9    Unknown World   45

10   Star Forge      50



*/

    if(nPlanetIndex == PLANET_ENDAR_SPIRE)

    {

        return 5;

    }

    else if(nPlanetIndex == PLANET_TARIS)

    {

        return 10;

    }

    else if(nPlanetIndex == PLANET_EBON_HAWK)

    {

        return -1;

    }

    else if(nPlanetIndex == PLANET_DANTOOINE)

    {

        return 15;

    }

    else if(nPlanetIndex == PLANET_TATOOINE)

    {

        return 35;

    }

    else if(nPlanetIndex == PLANET_KASHYYYK)

    {

        return 20;

    }

    else if(nPlanetIndex == PLANET_MANAAN)

    {

        return 25;

    }

    else if(nPlanetIndex == PLANET_KORRIBAN)

    {

        return 30;

    }

    else if(nPlanetIndex == PLANET_LEVIATHAN)

    {

        return 40;

    }

    else if(nPlanetIndex == PLANET_UNKNOWN_WORLD)

    {

        return 45;

    }

    else if(nPlanetIndex == PLANET_STAR_FORGE)

    {

        return 50;

    }

    else if(nPlanetIndex == PLANET_LIVE_01)

    {

        return 55;

    }

    else if(nPlanetIndex == PLANET_LIVE_02)

    {

        return 60;

    }

    else if(nPlanetIndex == PLANET_LIVE_03)

    {

        return 65;

    }

    else if(nPlanetIndex == PLANET_LIVE_04)

    {

        return 70;

    }

    else if(nPlanetIndex == PLANET_LIVE_05)

    {

        return 75;

    }

    return -1;

}



//::///////////////////////////////////////////////

//:: Start Render/Stunt Sequence

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Starts the correct sequence based on the

    planet being traveled to.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 9, 2002

//:://////////////////////////////////////////////



void EBO_PlayRenderSequence()

{

    int nSelected = GetSelectedPlanet();

    nSelected = EBO_GetPlanetFrom2DA(nSelected);

    SetGlobalNumber("K_FUTURE_PLANET", nSelected);

    int nCurrent = GetGlobalNumber("K_CURRENT_PLANET");

}



//::///////////////////////////////////////////////

//:: Should Bastila Start Vision Conversation

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This function returns true if bastila should

    start a cutscene dialogue with the PC

    You can use k_vis_[PLANET] == FALSE to see

    if they have been their before and seen the

    planet vision. This applies to Dantooine,

    Manaan, Korriban, Tatooine and Kashyyyk.



    Also set the script so that if Ebon_Vision !=99

    then it fires the dialog file ebo_bast_vision

    and has Bastila init dialog on the Ebon Hawk.

    (If Ebon_Vision==99 the dialog will not fire,

    but it should still play the vision.

    15 to 35

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 3, 2002

//:://////////////////////////////////////////////



int EBO_ShouldBastilaStartConversation()

{

    int nPlanet = GetGlobalNumber("K_CURRENT_PLANET");

    int nVision = GetGlobalNumber("Ebon_Vision");

    int nFLAG = FALSE;

    if( (nPlanet == 15 || nPlanet == 20 || nPlanet == 25 || nPlanet == 30 || nPlanet == 35) && nVision != 99)

    {

        //object oBast = GetNearestObjectByTag("Bastila");

        //if(GetIsObjectValid(oBast))

        //{

            if(nPlanet == 15 && !GetGlobalBoolean("k_vis_dantooine"))

            {

                nFLAG = TRUE;

                SetGlobalBoolean("k_vis_dantooine",1);

            }

            else if(nPlanet == 20 && !GetGlobalBoolean("k_vis_kashyyyk"))

            {

                nFLAG = TRUE;

                SetGlobalBoolean("k_vis_kashyyyk",1);

            }

            else if(nPlanet == 25 && !GetGlobalBoolean("k_vis_manaan"))

            {

                nFLAG = TRUE;

                SetGlobalBoolean("k_vis_manaan",1);

            }

            else if(nPlanet == 30 && !GetGlobalBoolean("k_vis_korriban"))

            {

                nFLAG = TRUE;

                SetGlobalBoolean("k_vis_korriban",1);

            }

            else if(nPlanet == 35 && !GetGlobalBoolean("k_vis_tatooine"))

            {

                nFLAG = TRUE;

                SetGlobalBoolean("k_vis_tatooine",1);

            }

            if(nFLAG == TRUE)

            {

                //AurPostString("k_vis_kashyyyk = " + IntToString(GetGlobalBoolean("k_vis_kashyyyk")), 5, 6, 3.0);

                //AurPostString("k_vis_manaan = " + IntToString(GetGlobalBoolean("k_vis_manaan")), 5, 7, 3.0);

                //AurPostString("k_vis_korriban = " + IntToString(GetGlobalBoolean("k_vis_korriban")), 5, 8, 3.0);

                //AurPostString("k_vis_tatooine = " + IntToString(GetGlobalBoolean("k_vis_tatooine")), 5, 9, 3.0);



                return TRUE;

                //HoldWorldFadeInForDialog();

                //object oPC = GetFirstPC();

                //AssignCommand(oBast, ActionStartConversation(oPC, "ebo_bast_vision", FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE));

            }

        //}

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Bastila Start Conversation

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: June 17,

//:://////////////////////////////////////////////



void EBO_BastilaStartConversation2()

{

    object oPC = GetFirstPC();

    object oBast = GetNearestObjectByTag("Bastila_Starter");

    if(GetIsObjectValid(oBast))

    {

        //AurPostString("Ebon_Vision = " + IntToString(GetGlobalNumber("Ebon_Vision")), 5, 6, 4.0);

        //AurPostString("Firing Bastila's Conversation", 5, 7, 4.0);

        AssignCommand(oBast, ActionStartConversation(oPC, "ebo_bast_vision", FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE, "Bastila"));

    }

}

''',

    'k_inc_end': b'''#include "k_inc_utility"

#include "k_inc_generic"



string sTraskTag = "end_trask";

string sTraskWP = "endwp_tarsk01";

string sCarthTag = "Carth";



string SOLDIER_WEAPON = "g_w_blstrrfl001";

string SOLDIER_ITEM01 = "g_i_adrnaline003";

string SOLDIER_ITEM02 = "";



string SCOUT_WEAPON = "g_w_blstrpstl001";

string SCOUT_ITEM01 = "g_i_adrnaline002";

string SCOUT_ITEM02 = "g_i_implant101";



string SCOUNDREL_WEAPON = "g_w_blstrpstl001";

string SCOUNDREL_ITEM01 = "g_i_secspike01";

string SCOUNDREL_ITEM02 = "g_i_progspike01";



int ROOM3_DEAD = 3;

int ROOM5_DEAD = 4;

int ROOM7_DEAD = 2;



int TRASK_DEFAULT = -1;

int TRASK_MUST_GET_GEAR = 0;

int TRASK_GEAR_DONE = 1;

int TRASK_TARGET_DONE = 2;

int TRASK_MUST_EQUIP = 3;

int TRASK_EQUIP_DONE = 4;

int TRASK_MUST_MAP = 5;

int TRASK_MAP_DONE = 6;

int TRASK_MUST_SWITCH = 7;

int TRASK_SWITCH_DONE = 8;

int TRASK_SWITCH_REMIND = 9;

int TRASK_CARTH_BRIDGE = 10;

int TRASK_BRIDGE_DONE = 11;

int TRASK_MUST_DOOR = 12;

int TRASK_DOOR_DONE = 13;

int TRASK_ROOM3_DONE = 14;

int TRASK_MUST_MEDPACK = 15;

int TRASK_COMBAT_WARNING = 16;

int TRASK_COMBAT_WARNING2 = 17;

int TRASK_COMPUTER_DONE = 18;

int TRASK_MUST_DROID = 19;

int TRASK_DROID_DONE = 20;

int TRASK_MUST_MAP_02 = 21;

int TRASK_NOTHING_02 = 22;

//int TRASK_COMBAT_WARNING = 27;

int TRASK_LEVEL_INIT = 28;

int TRASK_MUST_LEVEL = 29;

int TRASK_PARTY_LEVEL = 30;

int TRASK_LEVEL_DONE = 31;

string LOCKER_TAG = "end_locker01";

string STEALTH_UNIT = "g_i_belt010";

//returns Trask's object id

object GetTrask();



// checks if the conditions for passing the healing stage have been met

int HealingDone();



// returns Carth's object id

object GetCarth();



// checks if this has never been done before. uses sw 10

int HasNeverTriggered();



// Has Trask initiate with the pc at any distance

void TalkTrask();



// returns the effect from the corridor explosion

effect CorridorExplosion();



//spawns equipment into the first locker dependent on the players class

void SpawnStartingEquipment();



// returns if the door has been sliced (uses plot 2)

int GetIsSecureDoorSliced(object oDoor = OBJECT_SELF);



// sets the slice state of the door (uses plot 2)

void SetSecureDoorSliced(int bState, object oDoor = OBJECT_SELF);



// returns if the door has been repaired (uses plot 3)

int GetIsDamagedDoorRepaired(object oDoor = OBJECT_SELF);



// sets the repaired state of the door (uses plot 3)

void SetDamagedDoorRepaired(int bState, object oDoor = OBJECT_SELF);



// returns the value of the trask dialouge state global

int GetTraskState();



//sets the trask dialouge global

void SetTraskState(int nValue);



// returns true if there is somethin equipped in the weapon or body slots

int GetHasEquippedSomething();



// Checks if Trask is already waiting to initiate

int GetTraskWillInitiate();



// Sets the flag for Trask waiting to initiate

void SetTraskWillInitiate(int nValue);



//returns Carth dialgue state

int GetCarthState();



//sets Carth dialogue state

void SetCarthState(int nValue);



// plays an explosion

void PlayExplosion(string sWP = "end_explode01", int bWithShake = TRUE, int bWithRumble = TRUE);



//returns a cutscene invisible placeable based on the given number

object GetCutsceneObject(int nObjectNumber);

//////////////////////////////////////////////////////////////////////////





object GetTrask()

{

    return GetObjectByTag(sTraskTag);

}



int HealingDone()

{

    int bDone;

    object oPC = GetFirstPC();

    int bHasMedPack = GetIsObjectValid(GetItemPossessedBy(oPC,"g_i_medeqpmnt01"));

    int bFullHitPoints = GetCurrentHitPoints(oPC) == GetMaxHitPoints(oPC);

    if(bFullHitPoints || bHasMedPack == FALSE)

    {



        bDone = TRUE;

    }

    return bDone;

}



object GetCarth()

{

    return GetObjectByTag("Carth");

}



int HasNeverTriggered()

{

    int bReturn;

    if(UT_GetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_10) == FALSE)

    {

        bReturn = TRUE;

        UT_SetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_10,TRUE);

    }

    return bReturn;

}



void TalkTrask()

{

    object oTrask = GetTrask();

    if(GetPartyMemberByIndex(0) == oTrask)

    {

        SetPartyLeader(NPC_PLAYER);

    }

   // AurPostString("Trask trying to talk" + IntToString(GetTraskState()),5,5,5.0);

    NoClicksFor(0.5);

    DelayCommand(0.1,SignalEvent(oTrask,EventUserDefined(50)));

}



effect CorridorExplosion()

{

    effect eZap = EffectBeam(VFX_BEAM_LIGHTNING_DARK_L,GetObjectByTag("end_zap01"),BODY_NODE_CHEST);

    return EffectLinkEffects(EffectDamage(5),eZap);

}



object GetSpeaker()

{

    return GetPartyMemberByIndex(1);

}



object GetListener()

{

    return GetPartyMemberByIndex(0);

}



void SpawnStartingEquipment()

{

    object oLocker = GetObjectByTag(LOCKER_TAG);

    int nClass = GetClassByPosition(1,GetFirstPC());

    if(nClass == CLASS_TYPE_SCOUNDREL)

    {

        CreateItemOnObject(SCOUNDREL_WEAPON,oLocker);

        CreateItemOnObject(SCOUNDREL_ITEM01,oLocker);

        CreateItemOnObject(SCOUNDREL_ITEM02,oLocker);

    }

    else if(nClass == CLASS_TYPE_SCOUT)

    {

        CreateItemOnObject(SCOUT_WEAPON,oLocker);

        CreateItemOnObject(SCOUT_ITEM01,oLocker);

        CreateItemOnObject(SCOUT_ITEM02,oLocker);

    }

    else if(nClass == CLASS_TYPE_SOLDIER)

    {

        CreateItemOnObject(SOLDIER_WEAPON,oLocker);

        CreateItemOnObject(SOLDIER_ITEM01,oLocker);

        CreateItemOnObject(SOLDIER_ITEM02,oLocker);

    }



    if(GetHasSkill(SKILL_STEALTH,GetFirstPC()))

    {

        CreateItemOnObject(STEALTH_UNIT,oLocker);

    }

}



int GetIsSecureDoorSliced(object oDoor = OBJECT_SELF)

{

    return UT_GetPlotBooleanFlag(oDoor,SW_PLOT_BOOLEAN_02);

}



void SetSecureDoorSliced(int bState, object oDoor = OBJECT_SELF)

{

    UT_SetPlotBooleanFlag(oDoor,SW_PLOT_BOOLEAN_02,bState);

}



int GetIsDamagedDoorRepaired(object oDoor = OBJECT_SELF)

{

    return UT_GetPlotBooleanFlag(oDoor,SW_PLOT_BOOLEAN_03);

}



void SetDamagedDoorRepaired(int bState, object oDoor = OBJECT_SELF)

{

    UT_SetPlotBooleanFlag(oDoor,SW_PLOT_BOOLEAN_03,bState);

}



int GetTraskState()

{

    return GetGlobalNumber("END_TRASK_DLG");

}



void SetTraskState(int nValue)

{

  //  AurPostString("New State" + IntToString(nValue),5,7,2.0);

    SetGlobalNumber("END_TRASK_DLG",nValue);

   // AurPostString("Set: " + IntToString(nValue),5,10,3.0);

}



int GetHasEquippedSomething()

{

    int bItemEquipped = FALSE;

    object oPC = GetFirstPC();

    if(GetIsObjectValid(GetItemInSlot(INVENTORY_SLOT_RIGHTWEAPON,oPC)) ||

       GetIsObjectValid(GetItemInSlot(INVENTORY_SLOT_LEFTWEAPON,oPC)) ||

       GetIsObjectValid(GetItemInSlot(INVENTORY_SLOT_BODY,oPC)) )

    {

            bItemEquipped = TRUE;

    }

    return bItemEquipped;

}



int GetTraskWillInitiate()

{

    return UT_GetPlotBooleanFlag(GetTrask(),SW_PLOT_BOOLEAN_03);

}



void SetTraskWillInitiate(int nValue)

{

    UT_SetPlotBooleanFlag(GetTrask(),SW_PLOT_BOOLEAN_03,nValue);

}



int GetCarthState()

{

    return GetGlobalNumber("END_CARTH_DLG");

}



void SetCarthState(int nValue)

{

    SetGlobalNumber("END_CARTH_DLG",nValue);

}



void PlayExplosion(string sWP = "end_explode01", int bWithShake = TRUE, int bWithRumble = TRUE)

{

    location lExplode = GetLocation(GetNearestObjectByTag(sWP));

    effect eExplode = EffectVisualEffect(VFX_FNF_GRENADE_FRAGMENTATION);

    effect eShake = EffectVisualEffect(VFX_IMP_SCREEN_SHAKE);

    ApplyEffectAtLocation(DURATION_TYPE_INSTANT,eExplode,lExplode);

    if(bWithShake)

    {

        ApplyEffectToObject(DURATION_TYPE_INSTANT,eShake,GetFirstPC());

    }

    if(bWithRumble)

    {

        PlayRumblePattern(14);

    }

}



object GetCutsceneObject(int nObjectNumber)

{

    return GetObjectByTag("end01_sceneobj0" + IntToString(nObjectNumber));

}

''',

    'k_inc_endgame': b'''//::///////////////////////////////////////////////

//:: Name k_inc_endgame

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

     This include houses all of the stunt/render

     calls for the end game. This will be for

     modules sta_m45ac and sta_m45ad.

*/

//:://////////////////////////////////////////////

//:: Created By: Brad Prince

//:: Created On: Mar 6, 2003

//:://////////////////////////////////////////////



///////////////////////

// LIGHT SIDE scenes //

///////////////////////



// SCENE 1 BO2 - Player kills Bastila on sta_m45ac

void ST_PlayBastilaLight();

// SCENE 2 C01 - Player returns after watching SCENE 1.

void ST_PlayReturnToStarForgeLight();

// SCENE 3 A - Star Forge under attack.

void ST_PlayStarForgeUnderAttack();

// SCENE 4 B - End game credits - Light.

void ST_PlayEndCreditsLight();



//////////////////////////////////////////////////



//////////////////////

// DARK SIDE scenes //

//////////////////////



// SCENE 1 B01 - Bastila leaves party to meditate before generator puzzle.

void ST_PlayBastilaDark();

// SCENE 2 C - Player returns after watching SCENE 1.

void ST_PlayReturnToStarForgeDark();

// SCENE 3 A - The Republic dies.

void ST_PlayRepublicDies();

// SCENE 4 B - The Sith Ceremony.

void ST_PlaySithCeremony();

// SCENE 5 C - End game credits - Dark.

void ST_PlayEndCreditsDark();



//////////////////////////////////////////////////

//                  FUNCTIONS                   //

//////////////////////////////////////////////////



///////////////////////

// LIGHT SIDE scenes //

///////////////////////



// SCENE 1 BO2 - Player kills Bastila on sta_m45ac

void ST_PlayBastilaLight()

{

    StartNewModule("STUNT_50a","", "50b");

}



// SCENE 2 C01 - Player returns after watching SCENE 1.

void ST_PlayReturnToStarForgeLight()

{

    StartNewModule("sta_m45ac","K_LAST_LOCATION", "50");

}



// SCENE 3 A - Star Forge under attack.

void ST_PlayStarForgeUnderAttack()

{

    StartNewModule("STUNT_56a","", "56");

}



// SCENE 4 B - End game credits - Light.

void ST_PlayEndCreditsLight()

{

    StartNewModule("STUNT_57","", "56b");

}



//////////////////////////////////////////////////



//////////////////////

// DARK SIDE scenes //

//////////////////////



// SCENE 1 B01 - Bastila leaves party to meditate before generator puzzle.

void ST_PlayBastilaDark()

{

    StartNewModule("STUNT_51a","", "54");

}



// SCENE 2 C - Player returns after watching SCENE 1.

void ST_PlayReturnToStarForgeDark()

{

    StartNewModule("sta_m45ac","sta_bast_pc_move0", "51b");

}



// SCENE 3 A - The Republic dies.

void ST_PlayRepublicDies()

{

    StartNewModule("STUNT_54a","", "51");

}



// SCENE 4 B - The Sith Ceremony.

void ST_PlaySithCeremony()

{

    StartNewModule("STUNT_55a","", "54b");

}



// SCENE 5 C - End game credits - Dark.

void ST_PlayEndCreditsDark()

{

    StartNewModule("STUNT_57","", "56b");

}

''',

    'k_inc_force': b'''//:: k_inc_force

/*

    v1.0

    Force Powers Include for KOTOR

*/

//:: Created By: Preston Watamaniuk

//:: Copyright (c) 2002 Bioware Corp.



float fLightningDuration = 1.0;



//These variables are set in the script run area.

int SWFP_PRIVATE_SAVE_TYPE;

int SWFP_PRIVATE_SAVE_VERSUS_TYPE;

int SWFP_DAMAGE;

int SWFP_DAMAGE_TYPE;

int SWFP_DAMAGE_VFX;

int SWFP_HARMFUL;

int SWFP_SHAPE;



//Runs the script section for the particular force power.

void  Sp_RunForcePowers();

//Immunity and Resist Spell check for the force power.

//The eDamage checks whether the target is immune to the damage effect

int Sp_BlockingChecks(object oTarget, effect eEffect, effect eEffect2, effect eDamage);

//Makes the necessary saving throws

int Sp_MySavingThrows(object oTarget);

//Remove an effect of a specific type

void Sp_RemoveSpecificEffect(int nEffectTypeID, object oTarget);

//Remove an effect from a specific force power.

void Sp_RemoveSpellEffects(int nSpell_ID, object oCaster, object oTarget);

// Delays the application of a spell effect by an amount determined by distance.

float Sp_GetSpellEffectDelay(location SpellTargetLocation, object oTarget);

//Randomly delays the effect application for a default of 0.0 to 0.75 seconds

float Sp_GetRandomDelay(float fMinimumTime = 0.0, float MaximumTime = 0.75);

//Gets a saving throw appropriate to the jedi using the force power.

int Sp_GetJediDCSave();

///Apply effects in a sphere shape.

void Sp_SphereSaveHalf(object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration);

//Apply effects to a single target.

void Sp_SingleTarget(object oAnchor, effect eLink1, float fDuration1, effect eLink2, float fDuration2);

//Apply effect to an area and negate on a save.

void Sp_SphereBlocking(object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration);

// /Apply effect to an object and negate on a save.

void Sp_SingleTargetBlocking(object oAnchor, effect eLink1, float fDuration1, effect eLink2, float fDuration2);

//Apply effects for a for power.

void Sp_ApplyForcePowerEffects(float fTime, effect eEffect, object oTarget);

//Apply effects to targets.

void Sp_ApplyEffects(int nBlocking, object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration2, int nRacial = RACIAL_TYPE_ALL);

//Removes all effects from the spells , Knights Mind, Mind Mastery and Battle Meditation

void Sp_RemoveBuffSpell();

//Prints a string for the spell stript

void SP_MyPrintString(string sString);

//Posts a string for the spell script

void SP_MyPostString(string sString, int n1 = 5, int n2 = 10, float fTime = 4.0);

//Interates through given a time period and a damage amount and hurts someone.  Checks if the person is in conversation.

void SP_InterativeDamage(effect eDamage, int nSecondsRemaining, object oTarget);

//Checks to see if the target is a Turret

int SP_CheckAppearanceTurret(object oTarget, int nFeedback = FALSE);

//Checks to see if the target is a Mark 1, 2, 4 or Spyder Droid

int SP_CheckAppearanceGeoDroid(object oTarget);

//Checks if the character already has Energy Resistance and Improved Energy Resistance

int SP_CheckEnergyResistance(object oTarget);

//This checks all of the delayed effect applications to make sure the target is still hostile and has not surrendered

void SP_MyApplyEffectToObject(int nDurationType, effect eEffect, object oTarget, float fDuration=0.0);

//Checks droids appearance type and if they have shields up

int SP_CheckAppearanceGeoDroidShields(object oTarget, int nFeedback = FALSE);

//Check push compatibility, if true is passed in for the Whirlwind an addition check for shields is made

int SP_CheckForcePushViability(object oTarget, int Whirlwind);

//Removes the spell's effects regardless of caster

void Sp_RemoveSpellEffectsGeneral(int nSpell_ID, object oTarget);





//::///////////////////////////////////////////////

//:: Apply Delayed Effect

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This checks all of the delayed effect applications

    to make sure the target is still hostile and has

    not surrendered

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: May 20, 2003

//:://////////////////////////////////////////////

void SP_MyApplyEffectToObject(int nDurationType, effect eEffect, object oTarget, float fDuration=0.0)

{

    if(GetIsEnemy(oTarget))

    {

        ApplyEffectToObject(nDurationType, eEffect, oTarget, fDuration);

    }

}



//::///////////////////////////////////////////////

//:: Interative Damage

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Interates through given a time period and a

    damage amount and hurts someone.  Checks if

    the person is in conversation.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 5, 2003

//:://////////////////////////////////////////////

void SP_InterativeDamage(effect eDamage, int nSecondsRemaining, object oTarget)

{

    if(GetIsObjectValid(oTarget))

    {

        if(!GetIsConversationActive() && !GetIsDead(oTarget) && GetIsEnemy(oTarget))

        {

             if (nSecondsRemaining % 2 == 0)

             {

                  ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget);

             }

             --nSecondsRemaining;

             if (nSecondsRemaining > 0)

             {

                DelayCommand(1.0f, SP_InterativeDamage(eDamage, nSecondsRemaining, oTarget));

             }

        }

    }

}



//::///////////////////////////////////////////////

//:: Blocking Checks

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Does the Spell Resistance and Immunity

    Checks

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Aug 15, 2002

//:://////////////////////////////////////////////



int Sp_BlockingChecks(object oTarget, effect eEffect1, effect eEffect2, effect eDamage)

{

    int nReturn = FALSE;

    //MODIFIED by Preston Watamaniuk on April 11th

    //Put the immunity check in place for Force Powers.

    if(GetIsLinkImmune(oTarget, eEffect1) || GetIsLinkImmune(oTarget, eEffect2) || GetIsLinkImmune(oTarget, eDamage))

    {

        DisplayFeedBackText(oTarget, 1);

        nReturn = TRUE;

    }

    if(ResistForce(OBJECT_SELF, oTarget))

    {

        DisplayFeedBackText(oTarget, 0);

        nReturn = TRUE;

    }



    if(nReturn == TRUE)

    {

        ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceResisted(OBJECT_SELF), oTarget);

    }



    return nReturn;

}



int Sp_MySavingThrows(object oTarget)

{

    int nSave;

    if(SWFP_PRIVATE_SAVE_TYPE == SAVING_THROW_FORT)

    {

        nSave = FortitudeSave(oTarget, Sp_GetJediDCSave(), SWFP_PRIVATE_SAVE_VERSUS_TYPE);

        SP_MyPrintString("Fort Save = " + IntToString(nSave) + " For DC of " + IntToString(Sp_GetJediDCSave()));

    }

    else if(SWFP_PRIVATE_SAVE_TYPE == SAVING_THROW_REFLEX)

    {

        nSave = ReflexSave(oTarget, Sp_GetJediDCSave(), SWFP_PRIVATE_SAVE_VERSUS_TYPE);

        SP_MyPrintString("Reflex Save = " + IntToString(nSave)+" For DC of " + IntToString(Sp_GetJediDCSave()));

    }

    else if(SWFP_PRIVATE_SAVE_TYPE == SAVING_THROW_WILL)

    {

        nSave = WillSave(oTarget, Sp_GetJediDCSave(), SWFP_PRIVATE_SAVE_VERSUS_TYPE);

        SP_MyPrintString("Will Save = " + IntToString(nSave)+" For DC of " + IntToString(Sp_GetJediDCSave()));

    }

    if(nSave > 0)

    {

        ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceResisted(OBJECT_SELF), oTarget);

        DisplayFeedBackText(oTarget, 2);

    }

    return nSave;

}



void Sp_RemoveSpellEffects(int nSpell_ID, object oCaster, object oTarget)

{

    //Declare major variables

    int bValid = FALSE;

    effect eAOE;

    if(GetHasSpellEffect(nSpell_ID, oTarget))

    {

        //Search through the valid effects on the target.

        eAOE = GetFirstEffect(oTarget);

        while (GetIsEffectValid(eAOE) && bValid == FALSE)

        {

            //

            if (GetEffectCreator(eAOE) == oCaster)

            {

                //If the effect was created by the spell then remove it

                if(GetEffectSpellId(eAOE) == nSpell_ID)

                {

                    RemoveEffect(oTarget, eAOE);

                    bValid = TRUE;

                }

            }

            //Get next effect on the target

            eAOE = GetNextEffect(oTarget);

        }

    }

}



void Sp_RemoveSpellEffectsGeneral(int nSpell_ID, object oTarget)

{

    //Declare major variables

    int bValid = FALSE;

    effect eAOE;

    if(GetHasSpellEffect(nSpell_ID, oTarget))

    {

        //Search through the valid effects on the target.

        eAOE = GetFirstEffect(oTarget);

        while (GetIsEffectValid(eAOE) && bValid == FALSE)

        {

            //If the effect was created by the spell then remove it

            if(GetEffectSpellId(eAOE) == nSpell_ID)

            {

                RemoveEffect(oTarget, eAOE);

                bValid = TRUE;

            }

            //Get next effect on the target

            eAOE = GetNextEffect(oTarget);

        }

    }

}



void Sp_RemoveSpecificEffect(int nEffectTypeID, object oTarget)

{

    //Declare major variables

    //Get the object that is exiting the AOE

    int bValid = FALSE;

    effect eAOE;

    //Search through the valid effects on the target.

    eAOE = GetFirstEffect(oTarget);

    while (GetIsEffectValid(eAOE))

    {

        if (GetEffectType(eAOE) == nEffectTypeID)

        {

            //If the effect was created by the spell then remove it

            bValid = TRUE;

            RemoveEffect(oTarget, eAOE);

        }

        //Get next effect on the target

        eAOE = GetNextEffect(oTarget);

    }

}



float Sp_GetSpellEffectDelay(location SpellTargetLocation, object oTarget)

{

    float fDelay;

    return fDelay = GetDistanceBetweenLocations(SpellTargetLocation, GetLocation(oTarget))/20;

}



float Sp_GetRandomDelay(float fMinimumTime = 0.4, float MaximumTime = 1.1)

{

    float fRandom = MaximumTime - fMinimumTime;

    int nRandom;

    if(fRandom < 0.0)

    {

        return 0.0;

    }

    else

    {

        nRandom = FloatToInt(fRandom  * 10.0);

        nRandom = Random(nRandom) + 1;

        fRandom = IntToFloat(nRandom);

        fRandom /= 10.0;

        return fRandom + fMinimumTime;

    }

}



int Sp_GetJediDCSave()

{

    int nDC = GetSpellSaveDC();

    return nDC;

}



void Sp_ApplyForcePowerEffects(float fTime, effect eEffect, object oTarget)

{

    float fDelay;

    int nRoll = d6();

    fDelay = IntToFloat(nRoll)/10.0;

    if(fTime == 1000.0)

    {

        ApplyEffectToObject(DURATION_TYPE_PERMANENT, eEffect, oTarget);

    }

    else if(fTime == 0.0)

    {

        DelayCommand(fDelay, ApplyEffectToObject(DURATION_TYPE_INSTANT, eEffect, oTarget));

    }

    else

    {

        ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eEffect, oTarget, fTime);

    }

}



int SP_CheckEnergyResistance(object oTarget)

{

    if(GetHasSpellEffect(FORCE_POWER_RESIST_COLD_HEAT_ENERGY, oTarget) || GetHasSpellEffect(FORCE_POWER_RESIST_POISON_DISEASE_SONIC, oTarget))

    {

        return TRUE;

    }

    return FALSE;

}

//::///////////////////////////////////////////////

//:: Runs the specified force power.

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Runs the script for the particular force power.



    SWFP_HARMFUL = ;

    SWFP_PRIVATE_SAVE_TYPE;

    SWFP_PRIVATE_SAVE_VERSUS_TYPE;

    SWFP_DAMAGE;

    SWFP_DAMAGE_TYPE;

    SWFP_DAMAGE_VFX;



*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: July 30, 2002

//:://////////////////////////////////////////////



void  Sp_RunForcePowers()

{

    object oTarget = GetSpellTargetObject();

    effect eLink1, eLink2;

    effect eInvalid;

    SWFP_SHAPE = SHAPE_SPHERE;



    //P.W. (June 8) This makes the Taris Calo Nord immune to Force Push, breaks the cutscene if not.

    if(GetTag(oTarget) == "Calo082" && GetSpellId() == FORCE_POWER_FORCE_PUSH)

    {

        DisplayFeedBackText(oTarget, 1);

        return;

    }



    switch (GetSpellId())

    {

        /*

        AFFLICTION

        */

        case FORCE_POWER_AFFLICTION:

        {

            /*

            SWFP_HARMFUL = TRUE;

            eLink1 = EffectPoison(POISON_ABILITY_SCORE_AVERAGE);

            effect eLink3 = EffectLinkEffects(eLink1, EffectMovementSpeedDecrease(50));



            eLink3 = SetEffectIcon(eLink3, 1);

            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

            ApplyEffectToObject(DURATION_TYPE_PERMANENT, eLink1, oTarget);

            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink3, oTarget, 21.0);

            */

            SWFP_HARMFUL = TRUE;



            eLink1 = EffectPoison(POISON_ABILITY_SCORE_AVERAGE);

            eLink1 = EffectLinkEffects(eLink1, EffectMovementSpeedDecrease(50));

            eLink1 = SetEffectIcon(eLink1, 23);

            if(!GetIsPoisoned(oTarget))

            {

                Sp_ApplyEffects(FALSE, oTarget, 0.0, 1, eLink1, 1000.0, eInvalid, 0.0);

            }



        }

        break;



        /*

        CHOKE

        */

        case FORCE_POWER_CHOKE:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_FORT;

            SWFP_DAMAGE = (GetHitDice(OBJECT_SELF)*2)/3;

            SWFP_DAMAGE_TYPE = DAMAGE_TYPE_BLUDGEONING;

            SWFP_DAMAGE_VFX = VFX_IMP_CHOKE;



            eLink1 = EffectAbilityDecrease(ABILITY_CONSTITUTION, 4);

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityDecrease(ABILITY_STRENGTH, 4));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityDecrease(ABILITY_DEXTERITY, 4));

            eLink1 = SetEffectIcon(eLink1, 3);



            effect eChoke = EffectChoke();

            effect eDamage = EffectDamage(SWFP_DAMAGE, SWFP_DAMAGE_TYPE);



            int nResist = Sp_BlockingChecks(oTarget, eChoke, eDamage, eInvalid);

            int nSaves;

            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

            if(nResist == 0)

            {

                nSaves = Sp_MySavingThrows(oTarget);

                if(nSaves == 0)

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(VFX_IMP_CHOKE), oTarget);

                    ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eChoke, oTarget, 6.0);

                    ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oTarget, 24.0);

                    int nIdx = 1;

                    float fDelay;

                    SP_InterativeDamage(eDamage, 7, oTarget);

                }

            }

            if(nResist > 0 || nSaves > 0)

            {

                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

            }

        }

        break;



        /*

        CURE

        */

        //MODIFIED by Preston Watamaniuk March 28

        // Remove cure poison and reduced the amount by 5

        case FORCE_POWER_CURE:

        {

            SWFP_HARMFUL = FALSE;



            int nHeal = GetAbilityModifier(ABILITY_WISDOM) + GetAbilityModifier(ABILITY_CHARISMA) + 5 + GetHitDice(OBJECT_SELF);



            effect eVis =  EffectVisualEffect(VFX_IMP_CURE);

            int nCnt = 0;



            object oParty;

            if(IsObjectPartyMember(OBJECT_SELF))

            {

                oParty = GetPartyMemberByIndex(nCnt);

            }

            else

            {

                oParty = OBJECT_SELF;

            }



            while(nCnt < 3)

            {

                if(GetIsObjectValid(oParty) &&

                   GetRacialType(oParty) != RACIAL_TYPE_DROID &&

                   GetDistanceBetween(OBJECT_SELF, oParty) < 15.0)

                {

                    SignalEvent(oParty, EventSpellCastAt(OBJECT_SELF, GetSpellId(), FALSE));

                    //Sp_RemoveSpecificEffect(EFFECT_TYPE_POISON, oParty);

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eVis, oParty);

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectHeal(nHeal), oParty);

                }

                nCnt++;

                if(IsObjectPartyMember(OBJECT_SELF))

                {

                   oParty = GetPartyMemberByIndex(nCnt);

                }

                else

                {

                   oParty = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_FRIEND, OBJECT_SELF, nCnt);

                }

            }

        }

        break;



        /*

        DEATH FIELD

        */

        case FORCE_POWER_DEATH_FIELD:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_FORT;

            SWFP_PRIVATE_SAVE_VERSUS_TYPE = SAVING_THROW_TYPE_DARK_SIDE;

            int nDamTest = GetHitDice(OBJECT_SELF);

            if(nDamTest > 10)

            {

                nDamTest = 10;

            }

            SWFP_DAMAGE = d4(nDamTest);

            SWFP_DAMAGE_TYPE = DAMAGE_TYPE_DARK_SIDE;

            SWFP_DAMAGE_VFX = VFX_PRO_DEATH_FIELD;



            int nHealCount;

            int nDamage = SWFP_DAMAGE/2;

            effect eDamage;

            effect eBeam = EffectBeam(VFX_BEAM_DEATH_FIELD_TENTACLE, OBJECT_SELF, BODY_NODE_HEAD);

            effect eVFX = EffectVisualEffect(VFX_PRO_DEATH_FIELD);



            object oTarget = GetFirstObjectInShape(SHAPE_SPHERE, 12.0, GetLocation(OBJECT_SELF), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            while(GetIsObjectValid(oTarget))

            {

                int nResist = Sp_BlockingChecks(oTarget, eLink1, eLink2, eDamage);

                if((GetRacialType(oTarget) == RACIAL_TYPE_HUMAN &&

                   GetRacialType(oTarget) != RACIAL_TYPE_DROID) || GetObjectType(oTarget) == OBJECT_TYPE_PLACEABLE)

                {

                    if(GetIsEnemy(oTarget))

                    {

                        SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                        if(nResist == 0)

                        {

                            int nSaves = Sp_MySavingThrows(oTarget);

                            if(nSaves == FALSE)

                            {

                                eDamage =  EffectDamage(SWFP_DAMAGE, SWFP_DAMAGE_TYPE);

                                nHealCount += SWFP_DAMAGE;

                            }

                            else

                            {

                                eDamage =  EffectDamage(nDamage, SWFP_DAMAGE_TYPE);

                                nHealCount += nDamage;

                            }

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eVFX, oTarget);

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget);

                            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eBeam, oTarget, fLightningDuration);

                        }

                        else

                        {

                            //effect eBeam2 = EffectBeam(VFX_BEAM_DEATH_FIELD_TENTACLE, OBJECT_SELF, BODY_NODE_HEAD, TRUE);

                            //ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eBeam, oTarget, fLightningDuration);

                        }

                    }

                }

                oTarget = GetNextObjectInShape(SHAPE_SPHERE, 12.0, GetLocation(OBJECT_SELF), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            }

            if(GetCurrentHitPoints(OBJECT_SELF) < GetMaxHitPoints(OBJECT_SELF) && nHealCount > 0)

            {

                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectHeal(nHealCount), OBJECT_SELF);

            }

        }

        break;



        /*

        DRAIN LIFE

        */

        case FORCE_POWER_DRAIN_LIFE:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_FORT;

            int nDam = GetHitDice(OBJECT_SELF);

            int nDamTest = GetHitDice(OBJECT_SELF);

            if(nDamTest > 10)

            {

                nDamTest = 10;

            }

            SWFP_DAMAGE = d4(nDamTest);

            SWFP_DAMAGE_TYPE= DAMAGE_TYPE_DARK_SIDE;

            SWFP_DAMAGE_VFX = VFX_PRO_DRAIN;

            //Set up the drain effect link for the target

            effect eBeam = EffectBeam(VFX_BEAM_DRAIN_LIFE, OBJECT_SELF, BODY_NODE_HAND);

            effect eVFX = EffectVisualEffect(SWFP_DAMAGE_VFX);

            //Set up the link to Heal the user by the same amount.

            effect eHeal;

            effect eDamage = EffectDamage(SWFP_DAMAGE, DAMAGE_TYPE_DARK_SIDE);



            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eBeam, oTarget, fLightningDuration);

            DelayCommand(0.3, ApplyEffectToObject(DURATION_TYPE_INSTANT, eVFX, oTarget));



            int nResist = Sp_BlockingChecks(oTarget, eDamage, eInvalid, eInvalid);



            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

            if(GetRacialType(oTarget) != RACIAL_TYPE_DROID)

            {

                if(nResist == 0)

                {

                    int nSaves = Sp_MySavingThrows(oTarget);

                    if(nSaves > 0)

                    {

                        SWFP_DAMAGE /= 2;

                    }

                    eDamage = EffectDamage(SWFP_DAMAGE,  DAMAGE_TYPE_DARK_SIDE);

                    if(GetCurrentHitPoints(OBJECT_SELF) < GetMaxHitPoints(OBJECT_SELF) && SWFP_DAMAGE > 0)

                    {

                        eHeal = EffectHeal(SWFP_DAMAGE);

                        ApplyEffectToObject(DURATION_TYPE_INSTANT, eHeal, OBJECT_SELF);

                    }

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget);

                }

                else

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

                }

            }

        }

        break;



        /*

        DESTROY DROID

        */

        case FORCE_POWER_DROID_DESTROY:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_REFLEX;

            SWFP_PRIVATE_SAVE_VERSUS_TYPE = SAVING_THROW_TYPE_ELECTRICAL;



            eLink1 = EffectBeam(VFX_BEAM_DROID_DESTROY, oTarget, BODY_NODE_CHEST);

            eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_PRO_LIGHTNING_L));



            eLink2 = EffectDroidStun();

            eLink2 = EffectLinkEffects(eLink2, EffectVisualEffect(1008));

            eLink2 = SetEffectIcon(eLink2, 5);



            effect eLink3 = EffectBeam(VFX_BEAM_DROID_DESTROY, OBJECT_SELF, BODY_NODE_HAND);

            eLink3 = EffectLinkEffects(eLink3, EffectVisualEffect(VFX_PRO_LIGHTNING_L));



            int nDamage = d6(GetHitDice(OBJECT_SELF));

            int nApply = nDamage/2;

            effect eDamage = EffectDamage(nDamage, DAMAGE_TYPE_ELECTRICAL);;

            effect eSaveDamage = EffectDamage(nApply, DAMAGE_TYPE_ELECTRICAL);





            //Apply Effects to the first droid targeted.

            int nResist = Sp_BlockingChecks(oTarget, eLink1, eLink2, eInvalid);

            int nSaves;

            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink3, oTarget, fLightningDuration);

            if(nResist == 0)

            {

                nSaves = Sp_MySavingThrows(oTarget);

                if(nSaves == 0)

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage , oTarget);

                    ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oTarget, 12.0);

                }

                else

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eSaveDamage , oTarget);

                }

            }

            else

            {

                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

            }



            //Start going through all hostile droids around the primary target

            object oSecond = GetFirstObjectInShape(SHAPE_SPHERE, 6.0, GetLocation(oTarget), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            while(GetIsObjectValid(oSecond))

            {

                if(oSecond != oTarget && GetIsEnemy(oSecond) && GetRacialType(oSecond) == RACIAL_TYPE_DROID)

                {

                    nResist = Sp_BlockingChecks(oSecond, eLink1, eLink2, eInvalid);



                    SignalEvent(oSecond, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));



                    if(nResist == 0)

                    {

                        nSaves = Sp_MySavingThrows(oSecond);

                        //Apply the beam effect and hit regardless because damage is still done.

                        ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oSecond, fLightningDuration);

                        if(nSaves == 0)

                        {

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage , oSecond);

                            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oSecond, 12.0);

                        }

                        else

                        {

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eSaveDamage , oSecond);

                        }

                    }

                }

                oSecond = GetNextObjectInShape(SHAPE_SPHERE, 6.0, GetLocation(oTarget), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            }

        }

        break;



        /*

        DISABLE DROID

        */

        case FORCE_POWER_DROID_DISABLE:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_REFLEX;

            SWFP_PRIVATE_SAVE_VERSUS_TYPE = SAVING_THROW_TYPE_ELECTRICAL;



            eLink1 = EffectBeam(VFX_BEAM_DROID_DESTROY, oTarget, BODY_NODE_CHEST);

            eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_PRO_LIGHTNING_L));



            eLink2 = EffectDroidStun();

            eLink2 = EffectLinkEffects(eLink2, EffectVisualEffect(1008));

            eLink2 = SetEffectIcon(eLink2, 4);



            effect eLink3 = EffectBeam(VFX_BEAM_DROID_DISABLE, OBJECT_SELF, BODY_NODE_HAND);

            eLink3 = EffectLinkEffects(eLink3, EffectVisualEffect(VFX_PRO_LIGHTNING_L));



            int nDamage = GetHitDice(OBJECT_SELF);

            int nApply = nDamage/2;

            effect eDamage = EffectDamage(nDamage, DAMAGE_TYPE_ELECTRICAL);;

            effect eSaveDamage = EffectDamage(nApply, DAMAGE_TYPE_ELECTRICAL);





            //Apply Effects to the first droid targeted.

            int nResist = Sp_BlockingChecks(oTarget, eLink1, eLink2, eInvalid);

            int nSaves;

            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink3, oTarget, fLightningDuration);

            if(nResist == 0)

            {

                nSaves = Sp_MySavingThrows(oTarget);

                if(nSaves == 0)

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage , oTarget);

                    ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oTarget, 12.0);

                }

                else

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eSaveDamage , oTarget);

                }

            }

            else

            {

                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

            }



            //Start going through all hostile droids around the primary target

            object oSecond = GetFirstObjectInShape(SHAPE_SPHERE, 5.0, GetLocation(oTarget), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            while(GetIsObjectValid(oSecond))

            {

                if(oSecond != oTarget && GetIsEnemy(oSecond) && GetRacialType(oSecond) == RACIAL_TYPE_DROID)

                {

                    nResist = Sp_BlockingChecks(oSecond, eLink1, eLink2, eInvalid);



                    SignalEvent(oSecond, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));



                    if(nResist == 0)

                    {

                        nSaves = Sp_MySavingThrows(oSecond);

                        //Apply the beam effect and hit regardless because damage is still done.

                        ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oSecond, fLightningDuration);

                        if(nSaves == 0)

                        {

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage , oSecond);

                            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oSecond, 12.0);

                        }

                        else

                        {

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eSaveDamage , oSecond);

                        }

                    }

                }

                oSecond = GetNextObjectInShape(SHAPE_SPHERE, 5.0, GetLocation(oTarget), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            }

        }

        break;



        /*

        STUN DROID

        */

        case FORCE_POWER_DROID_STUN:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_FORT;

            SWFP_PRIVATE_SAVE_VERSUS_TYPE = SAVING_THROW_TYPE_ELECTRICAL;

            SWFP_DAMAGE = GetHitDice(OBJECT_SELF);

            SWFP_DAMAGE_TYPE= DAMAGE_TYPE_ELECTRICAL;



            eLink1 = EffectBeam(2065, OBJECT_SELF, BODY_NODE_HAND); //P.W.(May 19, 2003) New Droid Stun Beam Effect added

            eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_PRO_LIGHTNING_S));

            eLink2 = EffectDroidStun();

            eLink2 = SetEffectIcon(eLink2, 30);

            eLink2 = EffectLinkEffects(eLink2, EffectVisualEffect(1007));  //P.W.(May 19, 2003) Linked the smoke to Link 2

            effect eDamage;



            int nResist = Sp_BlockingChecks(oTarget, eLink1, eLink2, eInvalid);

            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));



            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oTarget, fLightningDuration);



            if(nResist == 0)

            {

                int nSaves = Sp_MySavingThrows(oTarget);

                if(nSaves == 0)

                {

                    eDamage = EffectDamage(SWFP_DAMAGE, DAMAGE_TYPE_ELECTRICAL);

                    ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oTarget, 12.0);

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget);

                }

                else

                {

                    eDamage = EffectDamage(SWFP_DAMAGE/2, DAMAGE_TYPE_ELECTRICAL);

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget);

                }

            }

            else

            {

                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

            }

        }

        break;



        /*

        FEAR

        */

        case FORCE_POWER_FEAR:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_WILL;

            SWFP_PRIVATE_SAVE_VERSUS_TYPE = SAVING_THROW_TYPE_FEAR;



            eLink1 = EffectHorrified();

            eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(1041));

            eLink1 = SetEffectIcon(eLink1, 6);



            Sp_ApplyEffects(TRUE, oTarget, 0.0, 1, eLink1, 6.0, eInvalid, 0.0);

        }

        break;



        /*

        FORCE ARMOR

        */

        case FORCE_POWER_FORCE_ARMOR:

        {

            SWFP_HARMFUL = FALSE;

            eLink1 = EffectACIncrease(6, AC_DODGE_BONUS);

            eLink1 = EffectLinkEffects(eLink1, EffectSavingThrowIncrease(SAVING_THROW_ALL, 6));

            eLink1 = SetEffectIcon(eLink1, 7);

            eLink2 = EffectVisualEffect(VFX_PRO_FORCE_ARMOR);

            eLink2 = EffectLinkEffects(eLink2, EffectVisualEffect(VFX_PRO_FORCE_SHIELD));





            //MODIFIED by Preston Watamaniuk on March 12

            //Make sure these Force Powers do not stack

            /*

            if(!GetHasSpellEffect(FORCE_POWER_FORCE_AURA) &&

               !GetHasSpellEffect(FORCE_POWER_FORCE_ARMOR) &&

               !GetHasSpellEffect(FORCE_POWER_FORCE_SHIELD))

            {

                Sp_ApplyEffects(FALSE, oTarget, 0.0, 1, eLink1, 20.0, eLink2, 3.0);

            }

            */



            //Modified by Preston Watamaniuk on Sept 2

            //Make sure the old power is replaced by a new version if the same or more powerful

            if(GetHasSpellEffect(FORCE_POWER_FORCE_AURA))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_FORCE_AURA, oTarget);

            }

            else if(GetHasSpellEffect(FORCE_POWER_FORCE_SHIELD))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_FORCE_SHIELD, oTarget);

            }

            else if(GetHasSpellEffect(FORCE_POWER_FORCE_ARMOR))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_FORCE_ARMOR, oTarget);

            }

            Sp_ApplyEffects(FALSE, oTarget, 0.0, 1, eLink1, 20.0, eLink2, 3.0);

        }

        break;



        /*

        FORCE AURA

        */

        case FORCE_POWER_FORCE_AURA:

        {

            SWFP_HARMFUL = FALSE;

            eLink1 = EffectACIncrease(2, AC_DODGE_BONUS);

            eLink1 = EffectLinkEffects(eLink1, EffectSavingThrowIncrease(SAVING_THROW_ALL, 2));

            eLink1 = SetEffectIcon(eLink1, 8);

            eLink2 = EffectVisualEffect(VFX_PRO_FORCE_AURA);



            //Modified by Preston Watamaniuk on Sept 2

            //Make sure the old power is replaced by a new version if the same or more powerful

            if(GetHasSpellEffect(FORCE_POWER_FORCE_AURA))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_FORCE_AURA, oTarget);

            }



            //MODIFIED by Preston Watamaniuk on March 12

            //Make sure these Force Powers do not stack

            if(!GetHasSpellEffect(FORCE_POWER_FORCE_ARMOR) &&

               !GetHasSpellEffect(FORCE_POWER_FORCE_SHIELD))

            {

                Sp_ApplyEffects(FALSE, oTarget, 0.0, 1, eLink1, 20.0, eLink2, 3.0);

            }



        }

        break;



        /*

        FORCE BREACH

        */

        case FORCE_POWER_FORCE_BREACH:

        {

            effect eBuff = GetFirstEffect(oTarget);

            int bValid = FALSE;

            while(GetIsEffectValid(eBuff))

            {

                if(GetEffectSpellId(eBuff) == FORCE_POWER_FORCE_AURA ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_FORCE_SHIELD ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_FORCE_ARMOR ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_FORCE_MIND ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_KNIGHT_MIND ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_MIND_MASTERY ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_SPEED_BURST ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_KNIGHT_SPEED ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_SPEED_MASTERY ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_RESIST_COLD_HEAT_ENERGY ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_RESIST_POISON_DISEASE_SONIC ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_RESIST_FORCE ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_FORCE_IMMUNITY)

                 {

                    RemoveEffect(oTarget, eBuff);

                 }

                 eBuff = GetNextEffect(oTarget);

            }

            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId()));

            ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(VFX_IMP_FORCE_BREACH), oTarget);

        }

        break;



        /*

        FORCE IMMUNITY

        */

        case FORCE_POWER_FORCE_IMMUNITY:

        {

            SWFP_HARMFUL = FALSE;

            int nSR = 15 + GetHitDice(OBJECT_SELF);

            eLink1 = EffectForceResistanceIncrease(nSR);

            eLink1 = SetEffectIcon(eLink1, 9);

            eLink2 = EffectVisualEffect(VFX_PRO_RESIST_FORCE);

            if(GetHasSpellEffect(FORCE_POWER_RESIST_FORCE))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_RESIST_FORCE, oTarget);

            }

            else if(GetHasSpellEffect(FORCE_POWER_FORCE_IMMUNITY))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_FORCE_IMMUNITY, oTarget);

            }

            Sp_ApplyEffects(TRUE, oTarget, 0.0, 1, eLink1, 60.0, eLink2, 1.0);

        }

        break;



        /*

        FORCE PUSH

        */

        case FORCE_POWER_FORCE_PUSH:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_REFLEX;

            SWFP_DAMAGE = GetHitDice(OBJECT_SELF);

            SWFP_DAMAGE_TYPE = DAMAGE_TYPE_BLUDGEONING;



            eLink1 = EffectForcePushed();

            eLink2 = EffectStunned();

            eLink2 = SetEffectIcon(eLink2, 11);

            eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_IMP_FORCE_PUSH));

            effect eDamage = EffectDamage(GetHitDice(OBJECT_SELF), SWFP_DAMAGE_TYPE);



            int nResist = Sp_BlockingChecks(oTarget, eLink1, eLink2, eDamage);

            if(SP_CheckForcePushViability(oTarget, FALSE))

            {

                if(nResist == FALSE)

                {

                    int nSaves = Sp_MySavingThrows(oTarget);

                    if(nSaves == FALSE)

                    {

                        eDamage = EffectDamage(GetHitDice(OBJECT_SELF), SWFP_DAMAGE_TYPE);

                        DelayCommand(0.4, SP_MyApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget));

                        ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oTarget, 0.1);

                        DelayCommand(2.55, SP_MyApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oTarget, 2.0));

                    }

                    else

                    {

                        eDamage = EffectDamage(GetHitDice(OBJECT_SELF)/2, SWFP_DAMAGE_TYPE);

                        ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oTarget, 0.1);

                        ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget);

                        ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(VFX_IMP_FORCE_PUSH), oTarget);



                    }

                }

                else

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

                }

            }

        }

        break;



        /*

        FORCE VALOR

        */

        case FORCE_POWER_FORCE_MIND:

        {

            SWFP_HARMFUL = FALSE;

            SWFP_SHAPE = SHAPE_SPHERE;

            eLink1 = EffectSavingThrowIncrease(SAVING_THROW_FORT,2);

            eLink1 = EffectLinkEffects(eLink1, EffectSavingThrowIncrease(SAVING_THROW_REFLEX, 2));

            eLink1 = EffectLinkEffects(eLink1, EffectSavingThrowIncrease(SAVING_THROW_WILL, 2));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_CHARISMA, 2));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_CONSTITUTION, 2));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_DEXTERITY, 2));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_INTELLIGENCE, 2));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_STRENGTH, 2));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_WISDOM, 2));

            eLink2 = EffectVisualEffect(VFX_IMP_MIND_FORCE);

            eLink1 = SetEffectIcon(eLink1, 10);

            Sp_RemoveBuffSpell();

            Sp_ApplyEffects(FALSE, OBJECT_SELF, 30.0, 1000, eLink1, 20.0, eLink2, 0.0);

        }

        break;



        /*

        FORCE SHIELD

        */

        case FORCE_POWER_FORCE_SHIELD:

        {

            SWFP_HARMFUL = FALSE;

            eLink1 = EffectACIncrease(4, AC_DODGE_BONUS);

            eLink1 = EffectLinkEffects(eLink1, EffectSavingThrowIncrease(SAVING_THROW_ALL, 4));

            eLink1 = SetEffectIcon(eLink1, 12);

            eLink2 = EffectVisualEffect(VFX_PRO_FORCE_SHIELD);



            //Modified by Preston Watamaniuk on Sept 2

            //Make sure the old power is replaced by a new version if the same or more powerful

            if(GetHasSpellEffect(FORCE_POWER_FORCE_AURA))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_FORCE_AURA, oTarget);

            }

            else if(GetHasSpellEffect(FORCE_POWER_FORCE_SHIELD))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_FORCE_SHIELD, oTarget);

            }

            //MODIFIED by Preston Watamaniuk on March 12

            //Make sure these Force Powers do not stack

            if(!GetHasSpellEffect(FORCE_POWER_FORCE_ARMOR))

            {

                Sp_ApplyEffects(FALSE, oTarget, 0.0, 1, eLink1, 20.0, eLink2, 3.0);

            }

        }

        break;



        /*

        FORCE STORM

        */

        case FORCE_POWER_FORCE_STORM:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_WILL;

            int nDamage = GetHitDice(OBJECT_SELF);

            if(nDamage > 10)

            {

                nDamage = 10;

            }

            SWFP_DAMAGE = d6(nDamage);

            SWFP_DAMAGE_TYPE = DAMAGE_TYPE_ELECTRICAL;

            effect eBeam = EffectBeam(2061, OBJECT_SELF, BODY_NODE_HEAD);

            effect eVis = EffectVisualEffect(VFX_PRO_LIGHTNING_L);

            effect eForce;

            effect eDam;

            object oUse = GetFirstObjectInShape(SHAPE_SPHERE, 12.0, GetLocation(oTarget), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            while(GetIsObjectValid(oUse))

            {

                //Make Immunity Checks

                if(GetIsEnemy(oUse))

                {

                    SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                    if(!ResistForce(OBJECT_SELF, oUse))

                    {

                        ApplyEffectToObject(DURATION_TYPE_INSTANT, eVis, oUse);

                        ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eBeam, oUse, fLightningDuration);

                        if(!WillSave(oUse, Sp_GetJediDCSave()))

                        {

                            eDam = EffectDamage(SWFP_DAMAGE, SWFP_DAMAGE_TYPE);

                            eForce = EffectDamageForcePoints(SWFP_DAMAGE);

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eDam, oUse);

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eForce, oUse);

                        }

                        else

                        {

                            eDam = EffectDamage(SWFP_DAMAGE/2, SWFP_DAMAGE_TYPE);

                            eForce = EffectDamageForcePoints(SWFP_DAMAGE/2);

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eDam, oUse);

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eForce, oUse);

                        }

                    }

                    else

                    {

                        ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

                    }

                }

                oUse = GetNextObjectInShape(SHAPE_SPHERE, 12.0, GetLocation(oTarget), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            }

        }

        break;



        /*

        FORCE WAVE

        */

        case FORCE_POWER_FORCE_WAVE:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_REFLEX;

            SWFP_DAMAGE = GetHitDice(OBJECT_SELF) + GetHitDice(OBJECT_SELF)/2;

            SWFP_DAMAGE_TYPE = DAMAGE_TYPE_BLUDGEONING;

            effect eVis = EffectVisualEffect(VFX_IMP_FORCE_PUSH);

            eLink1 = EffectForcePushed();

            eLink2 = EffectStunned();

            eLink2 = SetEffectIcon(eLink2, 13);

            effect eDam;

            effect eForce;

            object oUse = GetFirstObjectInShape(SHAPE_SPHERE, 15.0, GetLocation(OBJECT_SELF), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            ApplyEffectAtLocation(DURATION_TYPE_INSTANT, EffectVisualEffect(VFX_FNF_FORCE_WAVE), GetLocation(OBJECT_SELF));

            while(GetIsObjectValid(oUse))

            {

                //Make Immunity Checks

                if(GetIsEnemy(oUse))

                {

                    SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                    if(!ResistForce(OBJECT_SELF, oUse))

                    {

                        ApplyEffectToObject(DURATION_TYPE_INSTANT, eVis, oUse);

                        if(!ReflexSave(oUse, Sp_GetJediDCSave()))

                        {

                            eDam = EffectDamage(SWFP_DAMAGE, SWFP_DAMAGE_TYPE);

                            DelayCommand(0.4, SP_MyApplyEffectToObject(DURATION_TYPE_INSTANT, eDam, oUse));



                            if(SP_CheckForcePushViability(oUse, FALSE))

                            {

                                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oUse, 0.2);

                            }

                            DelayCommand(2.55, SP_MyApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oUse, 6.0));

                        }

                        else

                        {

                            if(SP_CheckForcePushViability(oUse, FALSE))

                            {

                                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oUse, 0.2);

                            }

                            eDam = EffectDamage(SWFP_DAMAGE/2, SWFP_DAMAGE_TYPE);

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eDam, oUse);

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceResisted(OBJECT_SELF), oTarget);

                        }

                    }

                }

                oUse = GetNextObjectInShape(SHAPE_SPHERE, 15.0, GetLocation(OBJECT_SELF), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            }

        }

        break;



        /*

        FORCE WHIRLWIND

        */

        case FORCE_POWER_FORCE_WHIRLWIND:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_REFLEX;

            SWFP_DAMAGE = GetHitDice(OBJECT_SELF)/3;

            SWFP_DAMAGE_TYPE = DAMAGE_TYPE_BLUDGEONING;

            effect eDamage = EffectDamage(SWFP_DAMAGE, SWFP_DAMAGE_TYPE);



            //SP_MyPostString(IntToString(SP_CheckAppearanceGeoDroidShields(oTarget)),5,5,3.0);



            if(SP_CheckForcePushViability(oTarget, TRUE))

            {

                eLink1 = EffectWhirlWind();

                eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_IMP_FORCE_WHIRLWIND));

                eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_DUR_FORCE_WHIRLWIND));

                eLink1 = SetEffectIcon(eLink1, 14);



                int nResist = Sp_BlockingChecks(oTarget, eLink1, eDamage, eInvalid);

                int nSaves;

                SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                if(nResist == 0)

                {

                    nSaves = Sp_MySavingThrows(oTarget);

                    if(nSaves == 0)

                    {

                        ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oTarget, 9.0);

                        ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eDamage, oTarget);

                        int nIdx = 1;

                        float fDelay;

                        SP_InterativeDamage(eDamage, 13, oTarget);

                    }

                }

                if(nResist > 0 || nSaves > 0)

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

                }

            }

            //Force Push all enemies away from the target is they meet the conditions.

            SP_MyPrintString("");

            eLink2 = EffectForcePushTargeted(GetLocation(oTarget));

            object oSecond = GetFirstObjectInShape(SHAPE_SPHERE, 5.0, GetLocation(oTarget));

            while(GetIsObjectValid(oSecond))

            {

                if(SP_CheckForcePushViability(oSecond, FALSE) == TRUE && GetIsEnemy(oSecond, OBJECT_SELF) && oSecond != oTarget)

                {

                    //P.W. (June 8) - Put this check in so Calo Nord does not move during the fight on Taris

                    if(GetTag(oTarget) != "Calo082")

                    {

                        SignalEvent(oSecond, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                        int nResist2 = Sp_BlockingChecks(oSecond, eLink2,eInvalid,eInvalid);

                        if(nResist2 == 0)

                        {

                            int nSaves2 = Sp_MySavingThrows(oSecond);

                            if(nSaves2 == 0)

                            {

                                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oSecond, 0.2);

                            }

                        }

                    }

                }

                oSecond = GetNextObjectInShape(SHAPE_SPHERE, 5.0, GetLocation(oTarget));

                SP_MyPrintString("");

            }

        }

        break;



        /*

        HEAL

        */

        //MODIFIED by Preston Watamaniuk March 28

        //Cut the heal in half

        case FORCE_POWER_HEAL:

        {

            SWFP_HARMFUL = FALSE;



            int nHeal = GetAbilityModifier(ABILITY_WISDOM) + GetAbilityModifier(ABILITY_CHARISMA) + 10 + GetHitDice(OBJECT_SELF);



            effect eVis =  EffectVisualEffect(VFX_IMP_HEAL);

            int nCnt = 0;



            object oParty;

            if(IsObjectPartyMember(OBJECT_SELF))

            {

                oParty = GetPartyMemberByIndex(nCnt);

            }

            else

            {

                oParty = OBJECT_SELF;

            }



            while(nCnt < 3)

            {

                if(GetIsObjectValid(oParty) &&

                   GetRacialType(oParty) != RACIAL_TYPE_DROID &&

                   GetDistanceBetween(OBJECT_SELF, oParty) < 15.0)

                {

                    SignalEvent(oParty, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                    Sp_RemoveSpecificEffect(EFFECT_TYPE_POISON, oParty);

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eVis, oParty);

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectHeal(nHeal), oParty);

                }

                nCnt++;

                if(IsObjectPartyMember(OBJECT_SELF))

                {

                   oParty = GetPartyMemberByIndex(nCnt);

                }

                else

                {

                   oParty = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_FRIEND, OBJECT_SELF, nCnt, CREATURE_TYPE_RACIAL_TYPE, RACIAL_TYPE_HUMAN);

                }

            }

        }

        break;

        /*

        HORROR

        */

        case FORCE_POWER_HORROR:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_WILL;

            SWFP_PRIVATE_SAVE_VERSUS_TYPE = SAVING_THROW_TYPE_FEAR;



            eLink1 = EffectHorrified();

            eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(1042));

            eLink1 = SetEffectIcon(eLink1, 16);

            Sp_ApplyEffects(TRUE, oTarget, 5.0, 1000, eLink1, 12.0, eInvalid, 0.0, RACIAL_TYPE_HUMAN);

        }

        break;



        /*

        INSANITY

        */

        case FORCE_POWER_INSANITY:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_WILL;

            SWFP_PRIVATE_SAVE_VERSUS_TYPE = SAVING_THROW_TYPE_FEAR;



            eLink1 = EffectHorrified();

            eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(1043));

            eLink1 = SetEffectIcon(eLink1, 17);

            Sp_ApplyEffects(TRUE, oTarget, 10.0, 1000, eLink1, 12.0, eInvalid, 0.0, RACIAL_TYPE_HUMAN);



            //ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(1043), oTarget);



        }

        break;



        /*

        KILL

        */

        case FORCE_POWER_KILL:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_DAMAGE_TYPE = DAMAGE_TYPE_BLUDGEONING;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_FORT;

            effect eDeath = EffectDeath();

            effect eDamage;

            effect eChoke = EffectChoke();

            eChoke = SetEffectIcon(eChoke, 18);

            effect eVFX = EffectVisualEffect(VFX_IMP_CHOKE);



            int nResist = Sp_BlockingChecks(oTarget, eDeath, eDamage, eChoke);

            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

            if(nResist == 0)

            {

                int nSaves = Sp_MySavingThrows(oTarget);

                int nDamage = GetHitDice(OBJECT_SELF);

                ApplyEffectToObject(DURATION_TYPE_INSTANT, eVFX, oTarget);

                eDamage = EffectDamage(nDamage, DAMAGE_TYPE_BLUDGEONING);

                if(nSaves == 0)

                {

                    ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eChoke, oTarget, 6.0);

                    nDamage = (GetMaxHitPoints(oTarget))/2;

                    nDamage = nDamage/3;

                    //This will do damage over time to make the effect look more dramatic

                    eDamage = EffectDamage(nDamage, DAMAGE_TYPE_BLUDGEONING);

                    SP_InterativeDamage(eDamage, 7, oTarget);

                }

                else

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget);

                }



            }

            else

            {

                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

            }

        }

        break;



        /*

        KNIGHT VALOR

        */

        case FORCE_POWER_KNIGHT_MIND:

        {

            SWFP_HARMFUL = FALSE;

            SWFP_SHAPE = SHAPE_SPHERE;

            eLink1 = EffectSavingThrowIncrease(SAVING_THROW_ALL,3);

            eLink1 = EffectLinkEffects(eLink1, EffectSavingThrowIncrease(SAVING_THROW_ALL, 3));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_CHARISMA, 3));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_CONSTITUTION, 3));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_DEXTERITY, 3));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_INTELLIGENCE, 3));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_STRENGTH, 3));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_WISDOM, 3));

            eLink1 = EffectLinkEffects(eLink1, EffectImmunity(IMMUNITY_TYPE_POISON));

            eLink1 = SetEffectIcon(eLink1, 19);

            eLink2 = EffectVisualEffect(1033);



            Sp_RemoveBuffSpell();

            //Sp_SphereSaveHalf(OBJECT_SELF, 30.0, 1000, eLink1, 20.0);

            Sp_ApplyEffects(TRUE, OBJECT_SELF, 30.0, 1000, eLink1, 20.0, eLink2, 0.0);

        }

        break;



        /*

        LIGHTSABER THROW

        */

        case FORCE_POWER_LIGHT_SABER_THROW:

        {

            SWFP_HARMFUL = TRUE;



            eLink1 = EffectLightsaberThrow(oTarget);

            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, OBJECT_SELF, 3.0);

            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

        }

        break;

        /*

        ADVANCED LIGHTSABER THROW

        */

        case FORCE_POWER_LIGHT_SABER_THROW_ADVANCED:

        {

            SWFP_HARMFUL = TRUE;

            object oTarget2, oTarget3;

            oTarget2 = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_FRIEND, oTarget, 1);

            if(GetIsObjectValid(oTarget2) && GetDistanceBetween(oTarget, oTarget2) <= 5.0)

            {

                oTarget3 = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_FRIEND, oTarget, 2);

                if(GetIsObjectValid(oTarget3) && GetDistanceBetween(oTarget, oTarget3) <= 5.0)

                {

                    SP_MyPrintString("Target 1 = " + ObjectToString(oTarget) +

                                " Target 2 = " + ObjectToString(oTarget2) +

                                " Target 3 = " + ObjectToString(oTarget3));

                    eLink1 = EffectLightsaberThrow(oTarget, oTarget2, oTarget3);

                    SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                    SignalEvent(oTarget2, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                    SignalEvent(oTarget3, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                }

                else

                {

                    SP_MyPrintString("Target 1 = " + ObjectToString(oTarget) +

                                " Target 2 = " + ObjectToString(oTarget2));

                    eLink1 = EffectLightsaberThrow(oTarget, oTarget2);

                    SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                    SignalEvent(oTarget2, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                }

            }

            else

            {

                SP_MyPrintString("Target 1 = " + ObjectToString(oTarget));

                eLink1 = EffectLightsaberThrow(oTarget);

                oTarget2 = OBJECT_INVALID;

            }

            SP_MyPrintString("Apply Throwsaber Effect");

            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, OBJECT_SELF, 3.0);

            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

        }

        break;



        /*

        LIGHTNING

        */

        case FORCE_POWER_LIGHTNING:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_WILL;

            SWFP_PRIVATE_SAVE_VERSUS_TYPE = SAVING_THROW_TYPE_ELECTRICAL;

            int nDamage = GetHitDice(OBJECT_SELF);

            if(nDamage > 10)

            {

                nDamage = 10;

            }

            SWFP_DAMAGE = d6(nDamage);

            SWFP_DAMAGE_TYPE = DAMAGE_TYPE_ELECTRICAL;

            SWFP_DAMAGE_VFX = VFX_PRO_LIGHTNING_L; //1036 - With sound

            SWFP_SHAPE = SHAPE_SPELLCYLINDER;



            effect eLightning = EffectBeam(VFX_BEAM_LIGHTNING_DARK_L, OBJECT_SELF, BODY_NODE_HAND);



            effect eDam = EffectDamage(SWFP_DAMAGE, SWFP_DAMAGE_TYPE);

            object oUse = GetFirstObjectInShape(SWFP_SHAPE, 17.0, GetLocation(oTarget), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            effect eBump = EffectVisualEffect(SWFP_DAMAGE_VFX);

            int nCnt = 1;

            // This will need to be changed to a double while get nearest in shape script.

            //ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(1036), OBJECT_SELF);

            while(GetIsObjectValid(oUse))

            {

                if(GetIsEnemy(oUse))

                {

                    SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                    //Make Immunity Checks

                    if(!ResistForce(OBJECT_SELF, oUse))

                    {

                        ApplyEffectToObject(DURATION_TYPE_INSTANT, eBump, oUse);

                        if(!WillSave(oUse, Sp_GetJediDCSave(), SWFP_PRIVATE_SAVE_VERSUS_TYPE))

                        {

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eDam, oUse);

                            //ApplyEffectToObject(DURATION_TYPE_INSTANT, eForce, oUse);

                        }

                        else

                        {

                            SWFP_DAMAGE /= 2;

                            eDam = EffectDamage(SWFP_DAMAGE, SWFP_DAMAGE_TYPE);

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, eDam, oUse);



                        }

                        ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLightning, oUse, fLightningDuration);

                    }

                    else

                    {

                        ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

                        ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceResisted(OBJECT_SELF), oTarget);

                    }

                }

                nCnt++;

                oUse = GetNextObjectInShape(SWFP_SHAPE, 17.0, GetLocation(oTarget), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            }

        }

        break;



        /*

        MASTER VALOR

        */

        case FORCE_POWER_MIND_MASTERY:

        {

            SWFP_HARMFUL = FALSE;

            SWFP_SHAPE = SHAPE_SPHERE;

            eLink1 = EffectSavingThrowIncrease(SAVING_THROW_ALL,5);

            eLink1 = EffectLinkEffects(eLink1, EffectSavingThrowIncrease(SAVING_THROW_ALL, 5));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_CHARISMA, 5));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_CONSTITUTION, 5));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_DEXTERITY, 5));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_INTELLIGENCE, 5));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_STRENGTH, 5));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_WISDOM, 5));

            eLink1 = EffectLinkEffects(eLink1, EffectImmunity(IMMUNITY_TYPE_POISON));

            eLink1 = SetEffectIcon(eLink1, 21);

            eLink2 = EffectVisualEffect(VFX_IMP_MIND_MASTERY);



            Sp_RemoveBuffSpell();

            Sp_ApplyEffects(TRUE, OBJECT_SELF, 30.0, 1000, eLink1, 20.0, eLink2, 0.0);



        }

        break;



        /*

        PLAGUE

        */

        case FORCE_POWER_PLAGUE:

        {

            SWFP_HARMFUL = TRUE;



            eLink1 = EffectPoison(POISON_ABILITY_SCORE_VIRULENT);

            eLink1 = EffectLinkEffects(eLink1, EffectMovementSpeedDecrease(50));

            eLink1 = SetEffectIcon(eLink1, 23);

            if(!GetIsPoisoned(oTarget))

            {

                Sp_ApplyEffects(FALSE, oTarget, 0.0, 1, eLink1, 1000.0, eInvalid, 0.0);

            }

        }

        break;



        /*

        IMPROVED ENERGY RESISTANCE

        */

        case FORCE_POWER_RESIST_COLD_HEAT_ENERGY:

        {

            SWFP_HARMFUL = FALSE;



            eLink1 = EffectDamageResistance(DAMAGE_TYPE_COLD, 15);

            eLink1 = EffectLinkEffects(eLink1, EffectDamageResistance(DAMAGE_TYPE_FIRE, 15));

            eLink1 = EffectLinkEffects(eLink1, EffectDamageResistance(DAMAGE_TYPE_SONIC, 15));

            eLink1 = EffectLinkEffects(eLink1, EffectDamageResistance(DAMAGE_TYPE_BLASTER, 15));

            eLink1 = EffectLinkEffects(eLink1, EffectDamageResistance(DAMAGE_TYPE_ELECTRICAL, 15));

            eLink1 = EffectLinkEffects(eLink1, EffectImmunity(IMMUNITY_TYPE_POISON));

            eLink1 = SetEffectIcon(eLink1, 24);

            eLink2 = EffectVisualEffect(VFX_PRO_RESIST_POISON);

            if(!SP_CheckEnergyResistance(OBJECT_SELF) && !IsObjectPartyMember(OBJECT_SELF))

            {

                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, OBJECT_SELF, 120.0);

                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, OBJECT_SELF, 1.0);

            }

            else if(IsObjectPartyMember(OBJECT_SELF))

            {

                int nCnt = 0;

                object oParty;

                for(nCnt; nCnt < 3; nCnt++)

                {

                    oParty = GetPartyMemberByIndex(nCnt);

                    if(GetIsObjectValid(oParty))

                    {

                        if(!SP_CheckEnergyResistance(oParty))

                        {

                            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oParty, 120.0);

                            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oParty, 1.0);

                        }

                    }

                }

            }



            //Sp_ApplyEffects(FALSE, oTarget, 10.0, 3, eLink1, 120.0, eLink2, 1.0);

        }

        break;



        /*

        RESIST FORCE 1

        */

        case FORCE_POWER_RESIST_FORCE:

        {

            SWFP_HARMFUL = FALSE;

            int nSR = 10 + GetHitDice(OBJECT_SELF);

            eLink1 = EffectForceResistanceIncrease(nSR);

            eLink1 = SetEffectIcon(eLink1, 25);

            eLink2 = EffectVisualEffect(VFX_PRO_RESIST_FORCE);

            if(GetHasSpellEffect(FORCE_POWER_RESIST_FORCE))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_RESIST_FORCE, oTarget);

            }

            if(!GetHasSpellEffect(FORCE_POWER_FORCE_IMMUNITY))

            {

                Sp_ApplyEffects(TRUE, oTarget, 0.0, 1, eLink1, 60.0, eLink2, 1.0);

            }

        }

        break;



        /*

        RESIST ENERGY

        */



        case FORCE_POWER_RESIST_POISON_DISEASE_SONIC:

        {

            if(!SP_CheckEnergyResistance(OBJECT_SELF))

            {

                SWFP_HARMFUL = FALSE;

                eLink1 = EffectDamageResistance(DAMAGE_TYPE_COLD, 15);

                eLink1 = EffectLinkEffects(eLink1, EffectDamageResistance(DAMAGE_TYPE_FIRE, 15));

                eLink1 = EffectLinkEffects(eLink1, EffectDamageResistance(DAMAGE_TYPE_SONIC, 15));

                eLink1 = EffectLinkEffects(eLink1, EffectDamageResistance(DAMAGE_TYPE_ELECTRICAL, 15));

                eLink1 = SetEffectIcon(eLink1, 26);

                eLink2 = EffectVisualEffect(VFX_PRO_RESIST_ELEMENTS);

                Sp_ApplyEffects(FALSE, oTarget, 0.0, 1, eLink1, 120.0, eLink2, 1.0);

            }

        }

        break;



        /*

        SHOCK

        */

        case FORCE_POWER_SHOCK:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_WILL;

            SWFP_PRIVATE_SAVE_VERSUS_TYPE = SAVING_THROW_TYPE_ELECTRICAL;

            int nDamage = GetHitDice(OBJECT_SELF);

            if(nDamage > 10)

            {

                nDamage = 10;

            }

            SWFP_DAMAGE = d6(nDamage);

            SP_MyPostString(IntToString(SWFP_DAMAGE),5,5,4.0);

            SWFP_DAMAGE_TYPE = DAMAGE_TYPE_ELECTRICAL;

            SWFP_DAMAGE_VFX = VFX_PRO_LIGHTNING_S;

            effect eDamage = EffectDamage(SWFP_DAMAGE, DAMAGE_TYPE_ELECTRICAL);

            effect eDamage2 = EffectDamage(SWFP_DAMAGE/2, DAMAGE_TYPE_ELECTRICAL);



            int nSaves = Sp_MySavingThrows(oTarget);

            int nResist = Sp_BlockingChecks(oTarget, eDamage, eInvalid, eInvalid);

            eLink1 = EffectBeam(2066, OBJECT_SELF, BODY_NODE_HAND); //P.W.(May 19, 2003) Changed to Shock beam effect.



            if(nResist == 0)

            {

                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oTarget, fLightningDuration);

                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(VFX_PRO_LIGHTNING_S), oTarget);

                if(nSaves == 0)

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget);

                }

                else

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage2, oTarget);

                }

            }

            //Sp_ApplyEffects(FALSE, oTarget, 0.0, 1, eLink1, fLightningDuration, eInvalid, 0.0);

        }

        break;



        /*

        STASIS

        */

        case FORCE_POWER_HOLD:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_FORT;

            eLink1 = EffectParalyze();

            eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_DUR_HOLD));

            eLink1 = SetEffectIcon(eLink1, 15);



            eLink2 = EffectMovementSpeedDecrease(50);

            eLink2 = EffectLinkEffects(eLink2, EffectACDecrease(4));

            eLink2 = SetEffectIcon(eLink2, 15);



            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

            //Make Immunity Checks

            int nResist = Sp_BlockingChecks(oTarget, eLink1, eLink2, eInvalid);

            if(nResist == 0)

            {

                int nSaves = Sp_MySavingThrows(oTarget);

                if(nSaves == 0)

                {

                    ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oTarget, 12.0);

                }

                else

                {

                    ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oTarget, 12.0);

                }

            }

            else

            {

                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

            }

        }

        break;



        /*

        STASIS FIELD

        */

        case FORCE_POWER_SLEEP:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_FORT;



            eLink1 = EffectParalyze();

            eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_DUR_HOLD));

            eLink1 = SetEffectIcon(eLink1, 27);



            eLink2 = EffectMovementSpeedDecrease(50);

            eLink2 = EffectLinkEffects(eLink2, EffectACDecrease(4));

            eLink2 = SetEffectIcon(eLink2, 27);



            oTarget = GetFirstObjectInShape(SHAPE_SPHERE, 10.0, GetLocation(oTarget), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            while(GetIsObjectValid(oTarget))

            {

                if(GetIsEnemy(oTarget) && GetRacialType(oTarget) != RACIAL_TYPE_DROID)

                {

                    SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                    //Make Immunity Checks

                    int nResist = Sp_BlockingChecks(oTarget, eLink1, eLink2, eInvalid);

                    if(nResist == 0)

                    {

                        int nSaves = Sp_MySavingThrows(oTarget);

                        if(nSaves == 0)

                        {

                            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oTarget, 12.0);

                        }

                        else

                        {

                            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oTarget, 12.0);

                        }

                    }

                }

                oTarget = GetNextObjectInShape(SHAPE_SPHERE, 10.0, GetLocation(oTarget), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

            }

        }

        break;



        /*

        SLOW

        */

        case FORCE_POWER_SLOW:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_WILL;



            eLink1 = EffectMovementSpeedDecrease(50);

            eLink1 = EffectLinkEffects(eLink1, EffectACDecrease(2));

            eLink1 = EffectLinkEffects(eLink1, EffectAttackDecrease(2));

            //eLink1 = EffectLinkEffects(eLink1, EffectDamageDecrease(2));

            eLink1 = EffectLinkEffects(eLink1, EffectSavingThrowDecrease(SAVING_THROW_REFLEX,2));

            eLink2 = EffectVisualEffect(VFX_PRO_AFFLICT);

            eLink1 = SetEffectIcon(eLink1, 28);



            Sp_ApplyEffects(TRUE, oTarget, 0.0, 1, eLink1, 30.0, eLink2, 1.0);

        }

        break;

        /*

        BURST OF SPEED

        */

        case FORCE_POWER_SPEED_BURST:

        {

            if(!GetHasSpellEffect(FORCE_POWER_KNIGHT_SPEED) &&

               !GetHasSpellEffect(FORCE_POWER_SPEED_MASTERY))

            {

                SWFP_HARMFUL = FALSE;

                eLink1 = EffectMovementSpeedIncrease(99);

                eLink1 = EffectLinkEffects(eLink1, EffectACIncrease(2));

                eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_DUR_KNIGHTS_SPEED));

                eLink1 = SetEffectIcon(eLink1, 2);

                if(OBJECT_SELF == GetPartyMemberByIndex(0))

                {

                    eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_DUR_SPEED));

                }

                if(GetHasSpellEffect(FORCE_POWER_SPEED_BURST, oTarget))

                {

                    Sp_RemoveSpellEffectsGeneral(FORCE_POWER_SPEED_BURST, oTarget);

                }

                Sp_ApplyEffects(FALSE, OBJECT_SELF, 0.0, 1, eLink1, 36.0, eInvalid, 0.0);

            }

        }

        break;



        /*

        KNIGHT SPEED

        */

        case FORCE_POWER_KNIGHT_SPEED:

        {

            if(!GetHasSpellEffect(FORCE_POWER_SPEED_MASTERY))

            {

                SWFP_HARMFUL = FALSE;

                eLink1 = EffectMovementSpeedIncrease(99);

                eLink1 = EffectLinkEffects(eLink1, EffectACIncrease(4));

                eLink1 = EffectLinkEffects(eLink1, EffectModifyAttacks(1));

                eLink1 = SetEffectIcon(eLink1, 20);



                if(OBJECT_SELF == GetPartyMemberByIndex(0))

                {

                    eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_DUR_SPEED));

                    //eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_IMP_SPEED_KNIGHT));

                }



                if(GetHasSpellEffect(FORCE_POWER_SPEED_BURST, oTarget))

                {

                    Sp_RemoveSpellEffectsGeneral(FORCE_POWER_SPEED_BURST, oTarget);

                }

                if(GetHasSpellEffect(FORCE_POWER_KNIGHT_SPEED, oTarget))

                {

                    Sp_RemoveSpellEffectsGeneral(FORCE_POWER_KNIGHT_SPEED, oTarget);

                }

                Sp_ApplyEffects(FALSE, OBJECT_SELF, 0.0, 1, eLink1, 36.0, eInvalid, 0.0);

            }

        }

        break;



        /*

        MASTER SPEED

        */

        case FORCE_POWER_SPEED_MASTERY:

        {

            SWFP_HARMFUL = FALSE;

            eLink1 = EffectMovementSpeedIncrease(99);

            eLink1 = EffectLinkEffects(eLink1, EffectACIncrease(4));

            eLink1 = EffectLinkEffects(eLink1, EffectModifyAttacks(2));

            eLink1 = SetEffectIcon(eLink1, 22);



            if(OBJECT_SELF == GetPartyMemberByIndex(0))

            {

                eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_DUR_SPEED));

                //eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_IMP_SPEED_MASTERY));

            }

            if(GetHasSpellEffect(FORCE_POWER_SPEED_BURST, oTarget))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_SPEED_BURST, oTarget);

            }

            if(GetHasSpellEffect(FORCE_POWER_KNIGHT_SPEED, oTarget))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_KNIGHT_SPEED, oTarget);

            }

            if(GetHasSpellEffect(FORCE_POWER_SPEED_MASTERY, oTarget))

            {

                Sp_RemoveSpellEffectsGeneral(FORCE_POWER_SPEED_MASTERY, oTarget);

            }

            Sp_ApplyEffects(FALSE, OBJECT_SELF, 0.0, 1, eLink1, 36.0, eInvalid, 0.0);

        }

        break;



        /*

        STUN

        */

        case FORCE_POWER_STUN:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_FORT;

            SWFP_PRIVATE_SAVE_VERSUS_TYPE = SAVING_THROW_TYPE_MIND_AFFECTING;



            eLink1 = EffectStunned();

            //eLink1 = EffectLinkEffects(eLink1, EffectVisualEffect(VFX_DUR_HOLD));

            eLink1 = SetEffectIcon(eLink1, 29);



            eLink2 = EffectMovementSpeedDecrease(50);

            eLink2 = EffectLinkEffects(eLink2, EffectACDecrease(4));

            eLink1 = SetEffectIcon(eLink1, 29);



            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

            //Make Immunity Checks

            int nResist = Sp_BlockingChecks(oTarget, eLink1, eLink2, eInvalid);

            int nSaves;

            if(nResist == 0)

            {

                nSaves = Sp_MySavingThrows(oTarget);

                if(nSaves == 0)

                {

                    ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oTarget, 9.0);

                }

                else

                {

                    ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oTarget, 9.0);

                }

            }

            if(nResist > 0 || nSaves > 0)

            {

                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

            }

        }

        break;



        /*

        SUPRESS FORCE

        */

        case FORCE_POWER_SUPRESS_FORCE:

        {

            effect eBuff = GetFirstEffect(oTarget);

            int bValid = FALSE;

            while(GetIsEffectValid(eBuff))

            {

                if(GetEffectSpellId(eBuff) == FORCE_POWER_FORCE_AURA ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_FORCE_SHIELD ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_FORCE_MIND ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_KNIGHT_MIND ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_SPEED_BURST ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_KNIGHT_SPEED ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_RESIST_FORCE ||

                   GetEffectSpellId(eBuff) == FORCE_POWER_RESIST_POISON_DISEASE_SONIC)

                 {

                    RemoveEffect(oTarget, eBuff);

                 }

                 eBuff = GetNextEffect(oTarget);

            }

            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId()));

            ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(VFX_IMP_FORCE_BREACH), oTarget);

        }

        break;



        /*

        WOUND

        */

        case FORCE_POWER_WOUND:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_FORT;

            SWFP_DAMAGE = (GetHitDice(OBJECT_SELF)*2)/3;

            SWFP_DAMAGE_TYPE = DAMAGE_TYPE_BLUDGEONING;



            effect eChoke = EffectChoke();

            eChoke = SetEffectIcon(eChoke, 31);

            effect eDamage = EffectDamage(SWFP_DAMAGE, SWFP_DAMAGE_TYPE);



            int nResist = Sp_BlockingChecks(oTarget, eChoke, eDamage, eInvalid);

            int nSaves;

            SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

            if(nResist == 0)

            {

                nSaves = Sp_MySavingThrows(oTarget);

                if(nSaves == 0)

                {

                    ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(VFX_IMP_CHOKE), oTarget);

                    ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eChoke, oTarget, 6.0);

                    int nIdx = 1;

                    float fDelay;

                    SP_InterativeDamage(eDamage, 7, oTarget);

                }

            }

            if(nResist > 0 || nSaves > 0)

            {

                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

            }

        }

        break;



        case SPECIAL_ABILITY_BODY_FUEL:

        {

            effect eBody = EffectBodyFuel();

            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eBody, OBJECT_SELF, 30.0);

        }

        break;

        case SPECIAL_ABILITY_ENHANCED_SENSES:

        {

            effect eAC = EffectACDecrease(6);

            effect eAware = EffectSkillIncrease(SKILL_AWARENESS, 10);

            effect eSee = EffectTrueSeeing();

            eLink1 = EffectLinkEffects(eAC, eAware);

            eLink1 = EffectLinkEffects(eLink1, eAware);

            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, OBJECT_SELF, RoundsToSeconds(10));

            ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(VFX_IMP_MIND_FORCE), OBJECT_SELF);

        }

        break;



        case SPECIAL_ABILITY_PSYCHIC_STANCE:

        {

            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_WILL;

            SWFP_PRIVATE_SAVE_VERSUS_TYPE = SAVING_THROW_TYPE_MIND_AFFECTING;



            eLink1 = EffectPsychicStatic();

            Sp_ApplyEffects(TRUE, oTarget, 10.0, 1000, eLink1, 20.0, eInvalid, 0.0);

        }

        break;



        /*

        Rage

        This ability allows Zaalbar to fly into a rage.

        When Zaalbar flies into a rage he gains +4 to his Strength and Constitution.  He also gains a +2 bonus on

        Fortitude and Will saves.  While raging Zaalbar cannot use any skills.  He also has a -4 penalty to his Defense rating.

        Interface: Mystical.  It takes one round to initiate the rage.

        Prerequisites: Nothing.  This is a unique NPC power.

        */

        case SPECIAL_ABILITY_RAGE:

        {

            SWFP_HARMFUL = FALSE;

            eLink1 = EffectLinkEffects(eLink1, EffectSavingThrowIncrease(SAVING_THROW_FORT, 2));

            eLink1 = EffectLinkEffects(eLink1, EffectSavingThrowIncrease(SAVING_THROW_WILL, 2));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_CONSTITUTION, 4));

            eLink1 = EffectLinkEffects(eLink1, EffectAbilityIncrease(ABILITY_STRENGTH, 4));

            eLink1 = EffectLinkEffects(eLink1, EffectACDecrease(4));



            Sp_ApplyEffects(TRUE, OBJECT_SELF, 0.0, 1, eLink1, 30.0, eInvalid, 0.0);

        }

        break;



        case 83: //Monster Slam Attack

        {

            SP_MyPrintString("I am attempting to use monster slam");



            SWFP_HARMFUL = TRUE;

            SWFP_PRIVATE_SAVE_TYPE = SAVING_THROW_REFLEX;

            SWFP_DAMAGE = GetHitDice(OBJECT_SELF);

            SWFP_DAMAGE_TYPE = DAMAGE_TYPE_BLUDGEONING;



            eLink1 = EffectForcePushed();

            eLink2 = EffectStunned();

            effect eDamage = EffectDamage(GetHitDice(OBJECT_SELF), SWFP_DAMAGE_TYPE);



            if(!ReflexSave(oTarget, 15))

            {

                eDamage = EffectDamage(GetHitDice(OBJECT_SELF), SWFP_DAMAGE_TYPE);

                DelayCommand(0.5, SP_MyApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget));

                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oTarget, 0.25);

                DelayCommand(2.55, SP_MyApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink2, oTarget, 3.0));

            }

            else

            {

                eDamage = EffectDamage(GetHitDice(OBJECT_SELF)/2, SWFP_DAMAGE_TYPE);

                DelayCommand(0.5, SP_MyApplyEffectToObject(DURATION_TYPE_TEMPORARY, eLink1, oTarget, 0.25));

                ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget);

                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(VFX_IMP_FORCE_PUSH), oTarget);



            }

        }

        break;



        case 130: //Fire Breath Weapon

        {

            oTarget = GetSpellTargetObject();

            int nDC = 15;

            int nDamage = 40;

            effect eBeam = EffectBeam(2053, OBJECT_SELF, BODY_NODE_HEAD);

            effect eVFX = EffectVisualEffect(1039);

            effect eBump = EffectVisualEffect(2062);

            effect eHorror = EffectHorrified();

            eHorror = SetEffectIcon(eHorror, 57);

            ApplyEffectToObject(DURATION_TYPE_INSTANT, eVFX, oTarget);

            ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eBeam, oTarget, 1.0);

            if(GetHitDice(oTarget) < 7 || FortitudeSave(oTarget, 15) == FALSE)

            {

                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eHorror, oTarget, 3.0);

            }

            DelayCommand(0.33, SP_MyApplyEffectToObject(DURATION_TYPE_TEMPORARY, eBump, oTarget, 1.5));

            if(ReflexSave(oTarget, nDC, SAVING_THROW_TYPE_FIRE))

            {

                nDamage /= 2;

            }

            effect eDam = EffectDamage(nDamage, DAMAGE_TYPE_FIRE);

            ApplyEffectToObject(DURATION_TYPE_INSTANT, eDam, oTarget);

        }

        break;



        case 131:

        {

            int nVFX = 3002;

            int nDC = 15;

            effect eDex = EffectAbilityDecrease(ABILITY_DEXTERITY, 3);

            eDex = SetEffectIcon(eDex, 41);

            ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(nVFX), OBJECT_SELF);

            oTarget = GetFirstObjectInShape(SHAPE_SPHERE, 10.0, GetSpellTargetLocation());

            while(GetIsObjectValid(oTarget))

            {

                if(GetIsEnemy(oTarget))

                {

                    if(!FortitudeSave(oTarget, nDC, SAVING_THROW_TYPE_SONIC))

                    {

                        ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eDex, oTarget, 30.0);

                    }

                }

                oTarget = GetNextObjectInShape(SHAPE_SPHERE, 4.0, GetSpellTargetLocation());

            }

        }

    }

}



//::///////////////////////////////////////////////

//:: While Loop Effect Delivery

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Uses these values to deliver the effects in the

    loop.



    SWFP_PRIVATE_SAVE_TYPE;

    SWFP_PRIVATE_SAVE_VERSUS_TYPE;

    SWFP_DAMAGE;

    SWFP_DAMAGE_TYPE;

    SWFP_DAMAGE_VFX;

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Aug 2, 2002

//:://////////////////////////////////////////////



void Sp_ApplyEffects(int nBlocking, object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration2, int nRacial = RACIAL_TYPE_ALL)

{

    int nCnt = 0;

    object oTarget;

    //By setting the counter to 1 you specify a single target.

    //By setting the counter to 1000, you specify all targets in a shape.

    //By setting the counter to another number you specify that many targets maximum.

    if(nCounter > 1)

    {

        oTarget = GetFirstObjectInShape(SWFP_SHAPE, fSize, GetLocation(oAnchor));

    }

    else if(nCounter == 1)

    {

        oTarget = oAnchor;

    }

    while(GetIsObjectValid(oTarget) && nCnt < nCounter)

    {

        if(nRacial == GetRacialType(oTarget) || nRacial == RACIAL_TYPE_ALL)

        {

            int nIdx = 0; // Index for the for loop link application.

            effect eUse;  // Current effect to use

            float fUse;   // Current duration to use

            int nDamage;  // The damage as set from SWFP_DAMAGE

            int bFizzle;  // Tracks whether the Fizzle has played on the caster yet or not.

            effect eDamage; // The damage effect which will be linked after the saves are done and checked with blocking.

            if((GetIsEnemy(oTarget) && SWFP_HARMFUL == TRUE) || (GetIsFriend(oTarget) && SWFP_HARMFUL == FALSE))

            {

                SignalEvent(oTarget, EventSpellCastAt(OBJECT_SELF, GetSpellId(), SWFP_HARMFUL));

                //eDamage = EffectDamage(SWFP_DAMAGE, SWFP_DAMAGE_TYPE);

                int nResist = FALSE;

                int nSaves = -1;

                if(SWFP_HARMFUL == TRUE)

                {

                    nResist = Sp_BlockingChecks(oTarget, eLink1, eLink2, eDamage);

                }

                //By adding another index the number of links added to this function can increase.

                for(nIdx; nIdx <= 1; nIdx++)

                {

                    if(nIdx == 0)

                    {

                        eUse = eLink1;

                        fUse = fDuration1;

                    }

                    else

                    {

                        eUse = eLink2;

                        fUse = fDuration2;

                    }

                    if(nResist == FALSE)

                    {

                        //MODIFIED by Preston Watamaniuk March 23

                         //Moved the save call down to here from up above with the resist inorder to help

                         //feedback system not make useless save calls.

                        //MODIFIED by Preston Watamaniuk March 24

                         //Made the default value of nSave -1 so that I only do it once.

                        //MODIFIED by Preston Watamaniuk April 5

                         //Made sure to set nSaves to FALSE so that it would fall through the function.

                        if(SWFP_HARMFUL == TRUE && nSaves == -1)

                        {

                            nSaves = Sp_MySavingThrows(oTarget);

                        }

                        else

                        {

                            nSaves = FALSE;

                        }

                        if(nSaves == FALSE)

                        {

                            if(nIdx == 1 && SWFP_DAMAGE > 0)

                            //Damage effects are always linked to the eDamage effect which is kept seperate from

                            //all other eLink types coming in.

                            {

                                eDamage = EffectDamage(SWFP_DAMAGE, SWFP_DAMAGE_TYPE);

                                eDamage = EffectLinkEffects(eDamage, EffectVisualEffect(SWFP_DAMAGE_VFX));

                                ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget);

                            }

                            if(GetIsEffectValid(eUse))

                            {

                                Sp_ApplyForcePowerEffects(fUse, eUse, oTarget);

                            }

                        }

                        //If the blocking flag is true then do not apply any effects on a save.

                        else if(nSaves > 0 && nBlocking == FALSE)

                        {

                            if(nIdx == 1 && SWFP_DAMAGE > 0)

                            {

                                SWFP_DAMAGE /= 2;

                                eDamage = EffectDamage(SWFP_DAMAGE, SWFP_DAMAGE_TYPE);

                                eDamage = EffectLinkEffects(eDamage, EffectVisualEffect(SWFP_DAMAGE_VFX));

                                ApplyEffectToObject(DURATION_TYPE_INSTANT, eDamage, oTarget);

                            }

                            if(GetIsEffectValid(eUse))

                            {

                                Sp_ApplyForcePowerEffects(fUse, eUse, oTarget);

                            }

                        }

                    }

                    if(nResist > 0 || (nSaves > 0 && nBlocking > 0))

                    {

                        if(bFizzle == FALSE)

                        {

                            ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectForceFizzle(), OBJECT_SELF);

                            bFizzle = TRUE;

                        }

                    }

                }

                nCnt++;

            }

        }

        oTarget = GetNextObjectInShape(SWFP_SHAPE, fSize, GetLocation(oAnchor), FALSE, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);

    }

}



//::///////////////////////////////////////////////

//:: Remove Buff Bonuses

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Goes through and removes all of the bonuses

    from people in a 30m radius from Force Mind,

    Knight Mind, Mind Mastery and Battle Meditation

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Aug 7, 2002

//:://////////////////////////////////////////////

void Sp_RemoveBuffSpell()

{

    object oTarget = GetFirstObjectInShape(SHAPE_SPHERE, 30.0, GetLocation(OBJECT_SELF));

    while(GetIsObjectValid(oTarget))

    {

        if(GetFactionEqual(oTarget))

        {

            //Declare major variables

            int bValid = FALSE;

            effect eAOE;

            if(GetHasSpellEffect(FORCE_POWER_FORCE_MIND, oTarget) ||

               GetHasSpellEffect(FORCE_POWER_MIND_MASTERY, oTarget) ||

               GetHasSpellEffect(FORCE_POWER_KNIGHT_MIND, oTarget) ||

               GetHasSpellEffect(SPECIAL_ABILITY_BATTLE_MEDITATION, oTarget))

            {

                //Search through the valid effects on the target.

                eAOE = GetFirstEffect(oTarget);

                while (GetIsEffectValid(eAOE) && bValid == FALSE)

                {

                    //If the effect was created by the spell then remove it

                    if(GetEffectSpellId(eAOE) == FORCE_POWER_FORCE_MIND ||

                       GetEffectSpellId(eAOE) == FORCE_POWER_MIND_MASTERY ||

                       GetEffectSpellId(eAOE) == FORCE_POWER_KNIGHT_MIND ||

                       GetEffectSpellId(eAOE) == SPECIAL_ABILITY_BATTLE_MEDITATION)

                    {

                        RemoveEffect(oTarget, eAOE);

                    }

                    //Get next effect on the target

                    eAOE = GetNextEffect(oTarget);

                }

            }

        }

        oTarget = GetNextObjectInShape(SHAPE_SPHERE, 30.0, GetLocation(OBJECT_SELF));

    }

}



//::///////////////////////////////////////////////

//:: Check for Appearance Type Turret

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks to see if the target is a Turret

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 10, 2003

//:://////////////////////////////////////////////

int SP_CheckAppearanceTurret(object oTarget, int nFeedback = FALSE)

{

    int nCheck = FALSE;



    SP_MyPostString("Appearance = " + IntToString(GetAppearanceType(oTarget)));



    if(GetAppearanceType(oTarget) == 182 || GetAppearanceType(oTarget) == 183)

    {

        if(nFeedback == TRUE)

        {

            DisplayFeedBackText(oTarget, 1);

        }

        nCheck = TRUE;

    }

    return nCheck;

}



//::///////////////////////////////////////////////

//:: Check Droid Appearance Type

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks to see if the target is a Mark 1, 2, 4

    or Spyder Droid

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 10, 2003

//:://////////////////////////////////////////////

int SP_CheckAppearanceGeoDroid(object oTarget)

{

    int nCheck = FALSE;

    if(GetAppearanceType(oTarget) == 59 ||

       GetAppearanceType(oTarget) == 60 ||

       GetAppearanceType(oTarget) == 61 ||

       GetAppearanceType(oTarget) == 65)

    {

        nCheck = TRUE;

    }

    return nCheck;

}



//::///////////////////////////////////////////////

//:: Check Droid Appearance Type and and Shields

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks to see if the target is a Mark 1, 2, 4

    or Spyder Droid and has a shield activated

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 10, 2003

//:://////////////////////////////////////////////

int SP_CheckAppearanceGeoDroidShields(object oTarget, int nFeedback = FALSE)

{

    int nCheck = FALSE;

    if(GetAppearanceType(oTarget) == 59 ||

       GetAppearanceType(oTarget) == 60 ||

       GetAppearanceType(oTarget) == 61 ||

       GetAppearanceType(oTarget) == 65)

    {

        if(GetHasSpellEffect(110, oTarget) ||

           GetHasSpellEffect(111, oTarget) ||

           GetHasSpellEffect(112, oTarget) ||

           GetHasSpellEffect(113, oTarget) ||

           GetHasSpellEffect(114, oTarget) ||

           GetHasSpellEffect(115, oTarget))

         {

            if(nFeedback == TRUE)

            {

                DisplayFeedBackText(oTarget, 1);

            }



            nCheck = TRUE;

         }

    }

    return nCheck;

}



//::///////////////////////////////////////////////

//:: Force Push Viability

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns TRUE if the target can be force pushed

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: June 12, 2003

//:://////////////////////////////////////////////

int SP_CheckForcePushViability(object oTarget, int Whirlwind)

{

    int bValid = FALSE;



    SP_MyPrintString("Push Check Start");

    if(GetCreatureSize(oTarget) != CREATURE_SIZE_LARGE &&

       GetCreatureSize(oTarget) != CREATURE_SIZE_HUGE)

    {

        SP_MyPrintString("Size is OK");

        if(SP_CheckAppearanceTurret(oTarget) == FALSE)

        {

            SP_MyPrintString("I am not a turret");

            if((Whirlwind == TRUE && SP_CheckAppearanceGeoDroidShields(oTarget) == FALSE) ||

                Whirlwind == FALSE)

            {

                SP_MyPrintString("I am whirlwind without droid shiled or not whirlwind");

                if(GetCreatureMovmentType(oTarget) != MOVEMENT_SPEED_IMMOBILE)

                {

                    SP_MyPrintString("Returning Push True");

                    bValid = TRUE;

                }

            }

        }

    }



    if(bValid == FALSE)

    {

        DisplayFeedBackText(oTarget, 1);

    }

    return bValid;

}





void SP_MyPrintString(string sString)

{

    if(!ShipBuild())

    {

        sString = "SPELL GENERIC DEBUG STRING: " + sString;

        PrintString(sString);

    }

}



void SP_MyPostString(string sString, int n1 = 5, int n2 = 10, float fTime = 4.0)

{

    sString = "DEBUG: " + sString;

    AurPostString(sString,10,10,3.0);

}





''',

    'k_inc_generic': b'''//:: k_inc_generic

/*

    v1.5

    Generic Include for KOTOR

    Post Clean Up as of March 3, 2003

*/

//:: Created By: Preston Watamaniuk

//:: Copyright (c) 2002 Bioware Corp.



#include "k_inc_gensupport"

#include "k_inc_walkways"

#include "k_inc_drop"



struct tLastRound

{

    int nLastAction;

    int nLastActionID;

    int nLastTalentCode;

    object oLastTarget;

    int nTalentSuccessCode;

    int nIsLastTargetDebil;

    int nLastCombo;

    int nLastComboIndex;

    int nCurrentCombo;

    int nBossSwitchCurrent;

};



struct tLastRound tPR;



//LOCAL BOOLEANS RANGE FROM 0 to 96

int AMBIENT_PRESENCE_DAY_ONLY = 1;        //POSSIBLE CUT

int AMBIENT_PRESENCE_NIGHT_ONLY = 2;      //POSSIBLE CUT

int AMBIENT_PRESENCE_ALWAYS_PRESENT = 3;



int SW_FLAG_EVENT_ON_PERCEPTION =   20;

int SW_FLAG_EVENT_ON_ATTACKED   =   21;

int SW_FLAG_EVENT_ON_DAMAGED    =   22;

int SW_FLAG_EVENT_ON_FORCE_AFFECTED = 23;

int SW_FLAG_EVENT_ON_DISTURBED = 24;

int SW_FLAG_EVENT_ON_COMBAT_ROUND_END = 25;

int SW_FLAG_EVENT_ON_DIALOGUE    = 26;

int SW_FLAG_EVENT_ON_DEATH       = 27;

int SW_FLAG_EVENT_ON_HEARTBEAT   = 28;

//int SW_FLAG_AMBIENT_ANIMATIONS = 29;          located in k_inc_walkways

//int SW_FLAG_AMBIENT_ANIMATIONS_MOBILE = 30;   located in k_inc_walkways

int SW_FLAG_FAST_BUFF            = 31;   //POSSIBLE CUT

int SW_FLAG_ASC_IS_BUSY          = 32;   //POSSIBLE CUT

int SW_FLAG_ASC_AGGRESSIVE_MODE  = 33;   //POSSIBLE CUT

int SW_FLAG_AMBIENT_DAY_ONLY     = 40;   //POSSIBLE CUT

int SW_FLAG_AMBIENT_NIGHT_ONLY   = 43;   //POSSIBLE CUT

int SW_FLAG_EVENT_ON_SPELL_CAST_AT = 44;

int SW_FLAG_EVENT_ON_BLOCKED     = 45;

int SW_FLAG_ON_DIALOGUE_COMPUTER = 48;

int SW_FLAG_FORMATION_POSITION_0 = 49;   //POSSIBLE CUT

int SW_FLAG_FORMATION_POSITION_1 = 50;   //POSSIBLE CUT

int SW_FLAG_FORMATION_POSITION_2 = 51;   //POSSIBLE CUT

int SW_FLAG_FORMATION_POSITION_3 = 52;   //POSSIBLE CUT

int SW_FLAG_FORMATION_POSITION_4 = 53;   //POSSIBLE CUT

int SW_FLAG_FORMATION_POSITION_5 = 54;   //POSSIBLE CUT

int SW_FLAG_FORMATION_POSITION_6 = 55;   //POSSIBLE CUT

int SW_FLAG_FORMATION_POSITION_7 = 56;   //POSSIBLE CUT

int SW_FLAG_FORMATION_POSITION_8 = 57;   //POSSIBLE CUT

int SW_FLAG_FORMATION_POSITION_9 = 58;   //POSSIBLE CUT

//int SW_FLAG_TARGET_FRIEND      = 59;        Located in k_inc_gensupport

int SW_FLAG_COMMONER_BEHAVIOR    = 60;

int SW_FLAG_SPECTATOR_STATE      = 61;

int SW_FLAG_AI_OFF               = 62;

int SW_CANDEROUS_COMBAT_REGEN    = 63;

int SW_FLAG_BOSS_AI              = 64;

int SW_FLAG_SHIELD_USED          = 65;

int SW_FLAG_EVENT_ON_DIALOGUE_END = 66;

int SW_FLAG_RESISTANCES_APPLIED  = 67;

int SW_FLAG_EVENT_DIALOGUE_END   = 68;   //User defined event

//This flag is set when the creature percieves a hostile for the first time.

//Used to eliminate the delay a creature puts on his perception event when first seeing a hostile.

int SW_FLAG_STATE_AGITATED       = 69;

int SW_FLAG_MALAK_AI_ON          = 70;

int SW_FLAG_DYNAMIC_COMBAT_ZONE  = 71;

int SW_FLAG_EVENT_ON_DIALOGUE_INTERRUPT  = 72;



//TALENT ROUTINES

int GEN_TALENT_SUPRESS_FORCE = 1;

int GEN_TALENT_REMOVE_POISON = 2;

int GEN_TALENT_HEALING       = 3;

int GEN_TALENT_BUFF          = 4;



//Sets the NPC listening patterns for the purposes of shouts

void GN_SetListeningPatterns();

//Determines what combat actions the character is going to take.

void GN_DetermineCombatRound(object oIntruder = OBJECT_INVALID);

// Function used by the On Dialogue script to determine what to do when a NPC gets shout

void GN_RespondToShout(object oShouter, int nShoutIndex, object oIntruder = OBJECT_INVALID);

//Sets the day night patterns for the creature.  Uses the AMBIENCE_ constants.

void GN_SetDayNightPresence(int nPresenceSetting);

//Sets the attack target depending on whether oTarget or oIntruder is Valid

object GN_DetermineAttackTarget(object oIntruder = OBJECT_INVALID);

//Makes the character flee the center of an explosion

void GN_DodgeGrenade(object oIntruder);

//Resets the formation booleans on a character.

void GN_ResetFormationBooleans();

//Checks which position on a character is free.

void GN_MoveToFormation(object oAnchor, int nFormationType);

//Runs the default AI routine

int GN_RunDefaultAIRoutine(object oIntruder = OBJECT_INVALID);

//Runs the Aid AI routine

int GN_RunAidAIRoutine(object oIntruder = OBJECT_INVALID);

//Runs the Grenade Thrower AI

int GN_RunGrenadeAIRoutine(object oIntruder = OBJECT_INVALID);

//Runs the Jedi Support AI routine

int GN_RunJediSupportAIRoutine(object oIntruder = OBJECT_INVALID);

//Runs the Boss AI Routine

int GN_RunBossAIRoutine(object oIntruder = OBJECT_INVALID);

//Run Boss Grenade AI Routine

int GN_RunBossGrenadeAI();

//Run Boss AOE Force Power Routine

int GN_RunBossAOEPowerRoutine();

//Runs special AI just for Darth Malak on the Star Forge

int GN_RunMalakAIRoutine();

//Run Boss Targeted Routine

int GN_RunBossTargetedRoutine();

//Sets up struct tLastRound to allow for a single point of determination.

void GN_SetLastRoundData();

//Makes the person or droid activate a shield

int GN_ActivateForceField();

//Makes the person activate Resist Elements and Resist Force.

int GN_ActivateResistances();

//Resets a Droid to his deactivated animation

void GN_ResetDroidDeactivationState(object oDroid = OBJECT_SELF);

//Checks the target and the droid utility use to make sure they are compatible

talent GN_CheckDroidUtilityUsage(object oTarget, talent tUse);

//Checks the target and the force power to make sure that a lightsaber is not thrown from close range.

talent GN_CheckThrowLightSaberUsage(object oTarget, talent tUse);

//Checks the target and the force power to make sure that a non-droid force power is used against a droid

talent GN_CheckNonDroidForcePower(object oTarget, talent tUse);

//Performs a series of checks in case the combat portion of DetermineCombatRound falls through.

int GN_DoPostDCRChecks();

//A void version of do post DCR checks for use with action do command.

void GN_ActionDoPostDCRChecks();



//Determine Combat Round Targeting Funtions

//This function returns an object if OBJECT_SELF is poisoned, or if any party member is poisoned.

object GN_CheckIfPoisoned();

//This function returns an object if OBJECT_SELF is below 50% health, or if any party member is injured.

object GN_CheckIfInjured();

//This checks the last hostile target and determines the best attack action based on the last round.

int GN_GetAttackTalentCode(object oTarget);

//Pass in a talent type and a target to have object_self use the talent

int GN_TalentMasterRoutine(int nTalentConstant, object oTarget);

//Determines where in the current combo the character is and what to do next based on AI style, and combat info.

talent GN_GetComboMove(int nBoss = FALSE);

//Plays an Ambient Animation depending on the spawn in condition selected.

void GN_PlayAmbientAnimation();

// This causes peasants to flee when people

int GN_CommonAI();

//Should Commoners run away.  This returns a yes or no based on a set of conditions

int GN_CheckShouldFlee();





void GN_DetermineCombatRound(object oIntruder = OBJECT_INVALID)

{

    GN_MyPrintString("");

    GN_MyPrintString("GENERIC DEBUG *************** START DETERMINE COMBAT ROUND " + GN_ReturnDebugName(OBJECT_SELF));



    GN_SetLastRoundData();

    int nPartyAI = GetPartyAIStyle(); //Determines how the party should react to intruders

    int nNPC_AI = GetNPCAIStyle(OBJECT_SELF); //Determines how the individual should react in combat

    GN_MyPrintString("GENERIC DEBUG *************** AI STYLE = " + GN_ReturnAIStyle());

    if(!GN_GetSpawnInCondition(SW_FLAG_COMMONER_BEHAVIOR)

    && !GN_GetSpawnInCondition(SW_FLAG_SPECTATOR_STATE)

    && !GN_GetSpawnInCondition(SW_FLAG_AI_OFF)

    //MODIFIED by Preston Watamaniuk on March 27

    //Put this back in to cancel Determine Combat when user actions are present.

    && !GetUserActionsPending())

    {

        if(GetPartyMemberByIndex(0) != OBJECT_SELF && !GetPlayerRestrictMode())

        {

            if((IsObjectPartyMember(OBJECT_SELF) && !GetPlayerRestrictMode()) || !IsObjectPartyMember(OBJECT_SELF))

            {

                if(nNPC_AI == NPC_AISTYLE_MELEE_ATTACK)

                {

                    if(GetIsObjectValid(oIntruder))

                    {

                        ClearAllActions();

                        ActionAttack(oIntruder);

                        return;

                    }

                    else

                    {

                        object oDefault = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY);

                        if(GetIsObjectValid(oDefault))

                        {

                            ClearAllActions();

                            ActionAttack(oDefault);

                            return;

                        }

                    }

                    return;

                }

                //Always try and run a force field at the beginning of combat.

                if(GN_ActivateForceField() == TRUE)

                {

                    GN_MyPrintString("GENERIC DEBUG *************** Terminating AI from Shields");

                    return;

                }

                //Always try to use Force Resistance at the beginning of combat.

                if(GN_ActivateResistances() == TRUE){return;}



                //P.W. (June 9) - Malak AI put into the generics

                if(GN_GetSpawnInCondition(SW_FLAG_MALAK_AI_ON) == TRUE)

                {

                    if(GN_RunMalakAIRoutine() == TRUE){return;}

                }



                //If the boss flag is set then the creature will run the boss AI first.

                if(GN_GetSpawnInCondition(SW_FLAG_BOSS_AI) == TRUE)

                {

                    if(GN_RunBossAIRoutine(oIntruder) == TRUE){return;}

                }



                if(nNPC_AI == NPC_AISTYLE_DEFAULT_ATTACK)

                {

                     //ACTIVE

                     if(GN_RunDefaultAIRoutine(oIntruder) == TRUE)

                     {

                        return;

                     }

                }

                else if(nNPC_AI == NPC_AISTYLE_GRENADE_THROWER)

                {

                     //ACTIVE

                     if(GN_RunGrenadeAIRoutine(oIntruder) == TRUE){return;}

                }

                else if(nNPC_AI == NPC_AISTYLE_JEDI_SUPPORT)

                {

                     //ACTIVE

                     if(GN_RunJediSupportAIRoutine(oIntruder) == TRUE){return;}

                }

            }

        }

    }

    if(GN_DoPostDCRChecks())

    {

        GN_MyPrintString("GENERIC DEBUG *************** DETERMINE COMBAT ROUND END");

    }

    GN_MyPrintString("GENERIC DEBUG *************** WARNING DETERMINE COMBAT ROUND FAILURE");

}



//::///////////////////////////////////////////////

//:: Do Post Determine Combat Round Checks

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Performs a series of checks in case the combat

    portion of DetermineCombatRound falls through.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 25, 2003

//:://////////////////////////////////////////////

int GN_DoPostDCRChecks()

{

    GN_MyPrintString("GENERIC DEBUG *************** Post DCR Checks for " + GN_ReturnDebugName(OBJECT_SELF));

    if(GN_GetSpawnInCondition(SW_FLAG_COMMONER_BEHAVIOR) && !GN_GetSpawnInCondition(SW_FLAG_SPECTATOR_STATE))

    {

        //MODIFIED by Preston Watamaniuk on May 29, 2003

        //Changed the commoner subroutine to make sure it walks ways at the end of battles.

        if(GN_CommonAI())

        {

            return TRUE;

        }

    }

    else if(GN_GetSpawnInCondition(SW_FLAG_SPECTATOR_STATE))

    {

        GN_MyPrintString("GENERIC DEBUG *************** Clear 1000");

        ClearAllActions();

        return TRUE;

    }

    //If all combat actions fail, then return to Walkways

    //P.W.(May 22, 2003) - Added check to make sure a waypoint path is set out for the creature. If then do not clear all actions.

    if(!IsObjectPartyMember(OBJECT_SELF) && GN_CheckWalkWays(OBJECT_SELF) == TRUE)

    {

        GN_MyPrintString("GENERIC DEBUG *************** Clear 1100");

        ClearAllActions();

        //MODIFIED by Preston Watamaniuk on May15, 2003

        //Put this delay command in so that bark bubble do not disapear so quickly off conversations.

        DelayCommand(1.0, GN_WalkWayPoints());

        return TRUE;

    }

    else if(GetPartyMemberByIndex(0) != OBJECT_SELF &&

            !GetIsObjectValid(GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF,1, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN)) &&

            IsObjectPartyMember(OBJECT_SELF))

    {

        if(!GetSoloMode())

        {

            GN_PostString("NO TARGET: FOLLOW LEADER");

            CancelCombat(OBJECT_SELF);

            GN_MyPrintString("GENERIC DEBUG *************** Clear 1200");

            ClearAllActions();

            ActionFollowLeader();

        }

        return TRUE;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: GN_ActionDoPostDCRChecks

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    A form of the DCR checks that can be run as

    an actions.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: May 29, 2003

//:://////////////////////////////////////////////

void GN_ActionDoPostDCRChecks()

{

    int nx = GN_DoPostDCRChecks();

}



//:://////////////////////////////////////////////

//:: Run Default AI

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Runs the default AI for an NPC. Returns FALSE

    if they cannot do anything.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 9, 2002

//:://////////////////////////////////////////////

int GN_RunDefaultAIRoutine(object oIntruder)

{

    object oTarget, oClose;

    int nTalentCode;

    talent tUse;



    oTarget = GN_CheckIfPoisoned();

    if(GetIsObjectValid(oTarget))

    {

        if(GN_TalentMasterRoutine(GEN_TALENT_REMOVE_POISON, oTarget)) {return TRUE;}

    }

    oTarget = GN_CheckIfInjured();

    if(GetIsObjectValid(oTarget))

    {

        if(GN_TalentMasterRoutine(GEN_TALENT_HEALING, oTarget)) {return TRUE;}

    }



    tUse = GN_GetComboMove();



    int nFriend = GetLocalBoolean(OBJECT_SELF, SW_FLAG_TARGET_FRIEND);

    if(nFriend == TRUE)

    {

        if(GetNPCAIStyle(OBJECT_SELF) == NPC_AISTYLE_JEDI_SUPPORT)

        {

            oTarget = GetPartyMemberByIndex(0);

        }

        else

        {

            oTarget = OBJECT_SELF;

        }

    }

    else

    {

        oTarget = tPR.oLastTarget;

        oClose = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF,1, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);



        GN_MyPrintString("GENERIC DEBUG *************** Default AI Debug Start *************************");

        GN_MyPrintString("GENERIC DEBUG *************** Intruder    = " + GN_ReturnDebugName(oIntruder));

        GN_MyPrintString("GENERIC DEBUG *************** Last Target = " + GN_ReturnDebugName(oTarget));

        GN_MyPrintString("GENERIC DEBUG *************** Closest     = " + GN_ReturnDebugName(oClose));



        //GN_MyPrintString("GENERIC DEBUG *************** " + GN_ReturnDebugName(OBJECT_SELF) + "I see an enemy = " + IntToString(GetIsObjectValid(oClose)));



        //MODIFIED by Preston Watamaniuk on June 3, 2003

        //I put this check in to make sure the party members only attack what you want until that things dies or leaves.

        if(IsObjectPartyMember(OBJECT_SELF) && GetIsObjectValid(oTarget) && !GetIsDead(oTarget) && GetObjectSeen(oTarget))

        {

            oTarget = oTarget; //Just put this here to show that the target is being used.

        }

        //MODIFIED by Preston Watamaniuk on May 15, 2003

        //Made it so the intruder object is always used if they can be seen and are valid.

        else if(GetIsObjectValid(oIntruder) && GetObjectSeen(oIntruder))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Intruder becomes Target");

            oTarget = oIntruder;

        }

        else if(GetIsObjectValid(oClose) && GetObjectSeen(oClose))

        {

            if((!GetIsObjectValid(oTarget) ||

               !GetIsEnemy(oTarget) ||

               GetIsDead(oTarget) ||

               GetCurrentHitPoints(oTarget) < GetCurrentHitPoints(oClose)))

               {

                  GN_MyPrintString("GENERIC DEBUG *************** Closest becomes Target");

                  oTarget = oClose;

               }

        }

    }



    //MODIFIED by Preston Watamaniuk on April 22, 2003

    //Put this check in to allow Droids to use their special abilities in a more logical manner. Passes in the talent and the target

    //and double checks that the usage is logical.

    if(GetRacialType(OBJECT_SELF) == RACIAL_TYPE_DROID)

    {

        tUse = GN_CheckDroidUtilityUsage(oTarget, tUse);

    }

    tUse = GN_CheckThrowLightSaberUsage(oTarget, tUse);

    tUse = GN_CheckNonDroidForcePower(oTarget, tUse);



    GN_MyPrintString("GENERIC DEBUG *************** Default AI Debug End ***************************");



    GN_MyPrintString("GENERIC DEBUG *************** Target = " + GN_ReturnDebugName(oTarget) + " is Enemy: " + IntToString(GetIsEnemy(oTarget)));

    if(GetIsObjectValid(oTarget))

    {

        GN_MyPrintString("GENERIC DEBUG *************** Clear 1300");

        ClearAllActions();

        if(GN_EquipAppropriateWeapon())

        {

           GN_MyPrintString("GENERIC DEBUG *************** Switching Weapons");

        }



        if(GetIsTalentValid(tUse) && GetIsEnemy(oTarget))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Using Talent on Target");

            ActionUseTalentOnObject(tUse, oTarget);

            return TRUE;

        }

        else if(GetIsEnemy(oTarget))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Action Attack by Default");

            ActionAttack(oTarget);

            return TRUE;

        }

    }

    GN_MyPrintString("GENERIC DEBUG *************** Default AI has failed to do an action");

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Jedi Aid AI

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    AI that concentrates on keeping the party healed,

    poison free.  If the party is doing ok then the Jedi

    will attempt to use Force Powers. If they are unable

    to use force powers they will run default AI.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 20, 2003

//:://////////////////////////////////////////////



int GN_RunAidAIRoutine(object oIntruder = OBJECT_INVALID)

{

    object oPoisoned = GN_CheckIfPoisoned();

    if(GetIsObjectValid(oPoisoned))

    {

        if(GN_TalentMasterRoutine(GEN_TALENT_REMOVE_POISON, oPoisoned)) {return TRUE;}

    }

    object oInjured = GN_CheckIfInjured();

    if(GetIsObjectValid(oInjured))

    {

        if(GN_TalentMasterRoutine(GEN_TALENT_HEALING, oInjured)) {return TRUE;}

    }



    return GN_RunDefaultAIRoutine(oIntruder);

}



//::///////////////////////////////////////////////

//:: Grenade AI

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Trys to use a grenades on targets not surrounded

    by enemies

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 17, 2003

//:://////////////////////////////////////////////



int GN_RunGrenadeAIRoutine(object oIntruder = OBJECT_INVALID)

{

    if(IsObjectPartyMember(OBJECT_SELF) || d100() > 50)

    {

        int nDroid = FALSE;

        talent tUse;

        object oTarget = GN_FindGrenadeTarget();



        if(GetRacialType(oTarget) == RACIAL_TYPE_DROID)

        {

            nDroid = TRUE;

        }



        tUse = GN_GetGrenadeTalent(nDroid);



        if(GetIsObjectValid(oTarget) && GetIsTalentValid(tUse) && GetCreatureHasTalent(tUse))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Clear 1400");

            ClearAllActions();

            ActionUseTalentOnObject(tUse, oTarget);

            return TRUE;

        }

        GN_MyPrintString("GENERIC DEBUG *************** Grenade AI Failure");

        return GN_RunDefaultAIRoutine(oIntruder);

    }

    GN_MyPrintString("GENERIC DEBUG *************** Grenade AI Fall Through");

    return GN_RunDefaultAIRoutine(oIntruder);

}



//::///////////////////////////////////////////////

//:: Jedi Support

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This will make the Jedi use Force Powers before

    everything else.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 17, 2003

//:://////////////////////////////////////////////

int GN_RunJediSupportAIRoutine(object oIntruder = OBJECT_INVALID)

{

    object oPoisoned = GN_CheckIfPoisoned();

    talent tUse;

    object oTarget;



    //P.W (May 27, 2003) - Made a change so that Droids can use Jedi Support. Its just defaul AI with an AI check however.

    if(GetRacialType(OBJECT_SELF) == RACIAL_TYPE_DROID)

    {

        return GN_RunDefaultAIRoutine();

    }



    if(GN_TalentMasterRoutine(GEN_TALENT_BUFF, OBJECT_SELF))

    {

        return TRUE;

    }

    if(GetIsObjectValid(oPoisoned))

    {

        if(GN_TalentMasterRoutine(GEN_TALENT_REMOVE_POISON, oPoisoned)) {return TRUE;}

    }

    object oInjured = GN_CheckIfInjured();

    if(GetIsObjectValid(oInjured))

    {

        if(GN_TalentMasterRoutine(GEN_TALENT_HEALING, oInjured)) {return TRUE;}

    }



    oTarget = GN_FindAOETarget();

    GN_MyPrintString("GENERIC DEBUG *************** Jedi Support AI: AOE Target = " + GN_ITS(GetIsObjectValid(oTarget)));

    if(GetIsObjectValid(oTarget))

    {

        if(GetRacialType(oTarget) == RACIAL_TYPE_DROID)

        {

            tUse = GN_GetBossCombatMove(SW_BOSS_ATTACK_TYPE_FORCE_POWER, TRUE);

        }

        else

        {

            tUse = GN_GetBossCombatMove(SW_BOSS_ATTACK_TYPE_FORCE_POWER);

        }

    }

    else

    {

        GN_MyPrintString("GENERIC DEBUG *************** Jedi Support AI: Inside the Party AI Section");



        oTarget = GN_DetermineAttackTarget();



        GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Initial oFind Search = " + GN_ReturnDebugName(oTarget));



        if(GetIsObjectValid(oTarget))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Jedi Support AI: Valid oTarget Set As = " + GN_ReturnDebugName(oTarget));

            if(GetRacialType(oTarget) == RACIAL_TYPE_DROID)

            {

                tUse = GN_GetBossCombatMove(SW_BOSS_ATTACK_TYPE_NPC, TRUE);

            }

            else

            {

                tUse = GN_GetBossCombatMove(SW_BOSS_ATTACK_TYPE_NPC);

            }

        }

    }

    tUse = GN_CheckThrowLightSaberUsage(oTarget, tUse);

    tUse = GN_CheckNonDroidForcePower(oTarget, tUse);

    if(GetIsObjectValid(oTarget) && GetIsTalentValid(tUse))

    {

        GN_MyPrintString("GENERIC DEBUG *************** Clear 1450");

        ClearAllActions();

        ActionUseTalentOnObject(tUse, oTarget);

        return TRUE;

    }

    GN_MyPrintString("GENERIC DEBUG *************** Jedi Support AI: Fall Through");

    return GN_RunDefaultAIRoutine();

}



//::///////////////////////////////////////////////

//:: Boss AI: Grenade

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Run Boss Grenade AI Routine

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 2, 2003

//:://////////////////////////////////////////////

int GN_RunBossGrenadeAI()

{

    GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Grenade Function Starting");

    talent tUse;

    object oCheck = GN_FindGrenadeTarget();

    GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Grenade Target = " + GN_ITS(GetIsObjectValid(oCheck)));

    int nDroid;

    if(GetIsObjectValid(oCheck))

    {

         if(GetRacialType(oCheck) == RACIAL_TYPE_DROID)

         {

            nDroid == TRUE;

         }

         tUse = GN_GetBossCombatMove(SW_BOSS_ATTACK_TYPE_GRENADE, nDroid);

         if(GetIsTalentValid(tUse))

         {

            GN_MyPrintString("GENERIC DEBUG *************** Clear 1460");

            ClearAllActions();

            ActionUseTalentOnObject(tUse, oCheck);

            GN_MyPrintString("GENERIC DEBUG *************** Boss AI: AOE Success");

            return TRUE;

         }

    }

    GN_MyPrintString("GENERIC DEBUG *************** Boss AI: AOE Failure");

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Boss AI: AOE Power

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Run Boss AOE Force Power Routine

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 2, 2003

//:://////////////////////////////////////////////

int GN_RunBossAOEPowerRoutine()

{

    GN_MyPrintString("GENERIC DEBUG *************** Boss AI: AOE Function Starting");

    talent tUse;

    object oCheck = GN_FindAOETarget();

    GN_MyPrintString("GENERIC DEBUG *************** Boss AI: AOE Target = " + GN_ITS(GetIsObjectValid(oCheck)));

    int nDroid;

    if(GetIsObjectValid(oCheck))

    {

         if(GetRacialType(oCheck) == RACIAL_TYPE_DROID)

         {

            nDroid == TRUE;

         }

         tUse = GN_GetBossCombatMove(SW_BOSS_ATTACK_TYPE_FORCE_POWER, nDroid);

         if(GetIsTalentValid(tUse))

         {

            ClearAllActions();

            ActionUseTalentOnObject(tUse, oCheck);

            GN_MyPrintString("GENERIC DEBUG *************** Boss AI: AOE Success");

            return TRUE;

         }

    }

    GN_MyPrintString("GENERIC DEBUG *************** Boss AI: AOE Failure");

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Boss AI: Targeting

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This will make boss monsters use targeted

    super powers.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 2, 2003

//:://////////////////////////////////////////////

int GN_RunBossTargetedRoutine()

{

    GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Start Targeted Action Routine");

    talent tUse;

    object oTarget;

    int nDroid;

    int nRand = d6();

    int nCnt = 1;

    if(nRand < 4){nRand = 1;}

    if(nRand == 4){nRand = 2;}

    if(nRand == 5){nRand = 3;}

    if(nRand == 6){nRand = 4;}



    GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Get the #" + GN_ITS(nRand) + " target");



    object oFind = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF, nCnt, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

    GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Initial oFind Search = " + GN_ReturnDebugName(oFind));

    while(GetIsObjectValid(oFind) && nCnt <= nRand)

    {

        GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Valid oFind = " + GN_ReturnDebugName(oFind) + " nCnt = " + GN_ITS(nCnt));

        if(GetIsObjectValid(oFind))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Valid oTarget Set As = " + GN_ReturnDebugName(oFind));

            oTarget = oFind;

        }

        nCnt++;

        oFind = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF, nCnt, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

    }



    //DEBUG STATEMENTS

    int nX = TRUE;

    if(nX == TRUE)

    {

        if(GetIsTalentValid(tUse))

        {

            if(GetTypeFromTalent(tUse) == TALENT_TYPE_FEAT)

            {

                GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Talent Feat = " + GN_ITS(GetIdFromTalent(tUse)));

            }

            else if(GetTypeFromTalent(tUse) == TALENT_TYPE_FORCE)

            {

                GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Talent Power = " + GN_ITS(GetIdFromTalent(tUse)));

            }

        }

    }

    if(GetIsObjectValid(oTarget))

    {

        if(GetRacialType(oTarget) == RACIAL_TYPE_DROID)

        {

            GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Get Boss Combat Move AI Droid");

            nDroid = TRUE;

        }

        tUse = GN_GetBossCombatMove(SW_BOSS_ATTACK_TYPE_NPC, nDroid);

        

        tUse = GN_CheckThrowLightSaberUsage(oTarget, tUse);

        tUse = GN_CheckNonDroidForcePower(oTarget, tUse);

        

        //MODIFIED by Preston Watamaniuk on April 2, 2003

        //Added this check to make the Droid setting was used for non-specific attacks.

        GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Target = " + GN_ITS(GetIsObjectValid(oTarget)));

        GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Talent = " + GN_ITS(GetIsTalentValid(tUse)));

        if(GetIsTalentValid(tUse) && GetIsObjectValid(oTarget))

        {

            ClearAllActions();

            ActionUseTalentOnObject(tUse, oTarget);

            GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Targeted Power Success");

            return TRUE;

        }

    }

    GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Targeted Failure");

    return FALSE;

}





//::///////////////////////////////////////////////

//:: Boss AI

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This will make boss monsters buff themselves

    and use more force powers or utility devices

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 31, 2003

//:://////////////////////////////////////////////

int GN_RunBossAIRoutine(object oIntruder = OBJECT_INVALID)

{

    GN_MyPrintString("GENERIC DEBUG *************** Boss AI Start");



    object oTarget = GN_CheckIfInjured();

    if(GetIsObjectValid(oTarget))

    {

        if(GN_TalentMasterRoutine(GEN_TALENT_HEALING, oTarget)) {return TRUE;}

    }

    if(GN_EquipAppropriateWeapon())

    {

       GN_MyPrintString("GENERIC DEBUG *************** Switching Weapons");

    }



    if(GN_RunBossGrenadeAI() == TRUE) {return TRUE;}

    else if(GN_RunBossAOEPowerRoutine() == TRUE) {return TRUE;}

    else if(GN_RunBossTargetedRoutine() ==  TRUE) {return TRUE;}



    GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Fall Through");

    return GN_RunDefaultAIRoutine();

}





//::///////////////////////////////////////////////

//:: Malak AI

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This AI is just for Darth Malak on the Star

    Forge. It assumes there is only the PC and

    no one else.

    

    Malak's Force Powers

        Master Speed

        Force Push

        Throw Lightsaber (15)

        Affliction

        Force Resistance

        Imp. Energy Resist

        Lightning (15)

        Force Breach

        

    This routine is an add-on for boss ai.  It

    tests certain conditions that could be

    occurring in the Malak fight and reacts to them

    in a more agressive manner.



    1. K_END_JEDI_LEFT - Will track the total number

       of entombed Jedi left in the fight.

    2. K_END_MALAK_JEDI_USED - Will track the number

    of Jedi's Malak has personally used in the fight.



*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 29, 2003

//:://////////////////////////////////////////////

int GN_RunMalakAIRoutine()

{

    GN_MyPrintString("GENERIC DEBUG *************** Malak AI Start");

    int nJediLeft = GetGlobalNumber("K_END_JEDI_LEFT");

    int nMalakUsed = GetGlobalNumber("K_END_MALAK_JEDI_USED");

    object oPC = GetFirstPC();

    int bJedi, bDist, bAttack;

    float fDist = GetDistanceBetween(OBJECT_SELF, oPC);



    //Check to see if Malak need to become more aggressive

    //Test the number of Jedi to see if the player has used any

    if(((8 - nJediLeft) < nMalakUsed))

    {

        bJedi = TRUE;

    }

    //Check to see if the player is running away

    GN_MyPrintString("GENERIC DEBUG *************** Malak Distance to PC = " + FloatToString(GetDistanceBetween(OBJECT_SELF, oPC),4,4));

    if(fDist > 10.0)

    {

        bDist = TRUE;

    }

    if(bDist == TRUE)

    {

        /*

            AI REACTION 2 - Player is keeping his distance.

            1. Force Breach if the player is using speed

            OR

            2. Use Action Attack to Force Jump

        */

        GN_MyPrintString("GENERIC DEBUG *************** Clear 1480");

        ClearAllActions();

        if(GetHasSpellEffect(FORCE_POWER_SPEED_BURST, oPC) ||

           GetHasSpellEffect(FORCE_POWER_KNIGHT_SPEED, oPC) ||

           GetHasSpellEffect(FORCE_POWER_SPEED_MASTERY, oPC))

        {

            talent tBreach = TalentSpell(FORCE_POWER_FORCE_BREACH);

            if(GetIsTalentValid(tBreach))

            {

                GN_MyPrintString("GENERIC DEBUG *************** Using Breach");

                ActionUseTalentOnObject(tBreach, oPC);

            }

            bAttack = TRUE;

        }

        else

        {

            if(fDist > 10.0)

            {

                int nRoll = d3();

                int nPower = -1;

                if(nRoll == 1)

                {

                    nPower = FORCE_POWER_LIGHTNING;

                }

                else if(nRoll == 2)

                {

                    nPower = FORCE_POWER_LIGHT_SABER_THROW;

                }

                else if(nRoll > 2)

                {

                    bAttack = TRUE;

                }

                if(nPower != -1)

                {

                    talent tPower = TalentSpell(nPower);

                    if(GetIsTalentValid(tPower))

                    {

                        GN_MyPrintString("GENERIC DEBUG *************** Malak Using Force Power");

                        ActionUseTalentOnObject(tPower, oPC);

                        return TRUE;

                    }

                }

            }

            bAttack = TRUE;

        }

    }

    if(bAttack == TRUE)

    {

        GN_MyPrintString("GENERIC DEBUG *************** Malak Attacking");

        ActionAttack(oPC);

        return TRUE;

    }

    GN_MyPrintString("GENERIC DEBUG *************** Malak AI Drop Out");

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Shield Activation

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Organic Shields are 99 to 107

    Droid shields are 110 to 115



    Scans through all of the shield talents to

    see if the target has a shield to use. If the

    shield is used then the person will never use

    another one. Party members will never use this

    function.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 31, 2003

//:://////////////////////////////////////////////

int GN_ActivateForceField()

{

    GN_MyPrintString("GENERIC DEBUG *************** Starting Forcefield Search");

    GN_MyPrintString("GENERIC DEBUG *************** Shield Boolean (" + GN_ITS(SW_FLAG_SHIELD_USED) + ") = " + GN_ITS(GN_GetSpawnInCondition(SW_FLAG_SHIELD_USED)));

    if(GN_GetSpawnInCondition(SW_FLAG_SHIELD_USED) == FALSE && !IsObjectPartyMember(OBJECT_SELF))

    {

        int nCnt, nStop;

        int bValid = FALSE;

        talent tShield;

        if(GetRacialType(OBJECT_SELF) == RACIAL_TYPE_DROID)

        {

            nCnt = 110;

            nStop = 115;

        }

        else

        {

            nCnt = 99;

            nStop = 107;

        }



        while(bValid == FALSE && nCnt <= nStop)

        {

            tShield = TalentSpell(nCnt);

            if(GetCreatureHasTalent(tShield))

            {

                bValid = TRUE;

            }

            else

            {

                nCnt++;

            }

        }



        if(GetCreatureHasTalent(tShield))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Clear 1700");

            ClearAllActions();

            ActionUseTalentOnObject(tShield, OBJECT_SELF);

            GN_SetSpawnInCondition(SW_FLAG_SHIELD_USED);

            return TRUE;

        }

        else

        {

            GN_MyPrintString("GENERIC DEBUG *************** Forcefield Search Fallthrough");

            GN_SetSpawnInCondition(SW_FLAG_SHIELD_USED);

            return FALSE;

        }

    }

    GN_MyPrintString("GENERIC DEBUG *************** Forcefield Search Fallthrough");

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Resistance Activation

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    20 Resist Force

    41 Force Immunity

    Checks to see if the character has resist force

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 31, 2003

//:://////////////////////////////////////////////

//Makes the person activate Resist Elements and Resist Force.

int GN_ActivateResistances()

{

    int bValid = FALSE;

    if(GN_GetSpawnInCondition(SW_FLAG_RESISTANCES_APPLIED) == FALSE && !IsObjectPartyMember(OBJECT_SELF))

    {

        if(GetHitDice(GetFirstPC()) >= 15 || GN_GetSpawnInCondition(SW_FLAG_BOSS_AI))

        {

            talent tResist = TalentSpell(FORCE_POWER_RESIST_FORCE);

            talent tImmune = TalentSpell(FORCE_POWER_FORCE_IMMUNITY);

            talent tUse;

            if(GetCreatureHasTalent(tImmune))

            {

                tUse = tImmune;

                bValid = TRUE;

            }

            else if(GetCreatureHasTalent(tResist))

            {

                tUse = tResist;

                bValid = TRUE;

            }



            if(bValid == TRUE)

            {

                GN_MyPrintString("GENERIC DEBUG *************** Clear 1710");

                ClearAllActions();

                ActionUseTalentOnObject(tUse, OBJECT_SELF);

            }

            GN_SetSpawnInCondition(SW_FLAG_RESISTANCES_APPLIED);

        }

    }



    return bValid;

}







//:://///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//:://///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//:: Respond to Shout                                           ========  =       =   =======   =       =  =========   ========

//:: Copyright (c) 2001 Bioware Corp.                          =          =       =  =       =  =       =      =      =

//:://////////////////////////////////////////////             =          =       =  =       =  =       =      =      =

/*//                                                           =          =       =  =       =  =       =      =      =

    Catches the shouts and determines the best                 =========  =========  =       =  =       =      =      =========

    course of action for them                                          =  =       =  =       =  =       =      =              =

                                                                       =  =       =  =       =  =       =      =              =

    SetListenPattern(OBJECT_SELF, "GEN_I_WAS_ATTACKED", 1);            =  =       =  =       =  =       =      =              =

    SetListenPattern(OBJECT_SELF, "GEN_I_SEE_AN_ENEMY", 15);   ========   =       =   =======     ======       =      ========

*///

//:://///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: July 16, 2002

//:://///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//:://///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void GN_RespondToShout(object oShouter, int nShoutIndex, object oIntruder = OBJECT_INVALID)

{

    GN_MyPrintShoutString("");

    GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Respond to Shout Started for " + GN_ReturnDebugName(OBJECT_SELF));

    GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Intruder Object = " + GN_ReturnDebugName(oIntruder));



    int nFLAG; //This determines whether the object walksway points instead of attacking.

    int nPartyAI = GetPartyAIStyle(); //Determines how the party should react to intruders

    int nNPC_AI = GetNPCAIStyle(OBJECT_SELF); //Determines how the individual should react in combat



    //MODIFIED by Preston Watamaniuk May 9

    //Put this check into disable shouts being heard by people from different combat zones.

    if(GetLocalNumber(oShouter, SW_NUMBER_COMBAT_ZONE) == GetLocalNumber(OBJECT_SELF, SW_NUMBER_LAST_COMBO) ||

       GetLocalNumber(oShouter, SW_NUMBER_COMBAT_ZONE) == 0 ||

       GetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBAT_ZONE) == 0 ||

       IsObjectPartyMember(OBJECT_SELF))

    {

        if(!GN_GetSpawnInCondition(SW_FLAG_COMMONER_BEHAVIOR)

           && !GN_GetSpawnInCondition(SW_FLAG_SPECTATOR_STATE)

           && !GN_GetSpawnInCondition(SW_FLAG_AI_OFF)

           && !GetUserActionsPending())

        {

            GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Check 1 Pass");

            if(nShoutIndex == 1 && GetIsFriend(oShouter) && oShouter != OBJECT_SELF)

            {

                if((IsObjectPartyMember(OBJECT_SELF) && IsObjectPartyMember(oShouter) && GetSoloMode() == FALSE) ||

                    !IsObjectPartyMember(OBJECT_SELF))

                {

                    GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Check 2 Pass");

                    if(!GetIsObjectValid(GetAttemptedAttackTarget()) && !GetIsObjectValid(GetAttemptedSpellTarget()) && !GetIsObjectValid(GetAttackTarget()))

                    {

                        GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Check 3 Pass");

                        if(GetPartyMemberByIndex(0) != OBJECT_SELF && nPartyAI != PARTY_AISTYLE_PASSIVE && !GetPlayerRestrictMode())

                        {

                            GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Check 3 Pass");

                            if((IsObjectPartyMember(OBJECT_SELF) && !GetPlayerRestrictMode()) || !IsObjectPartyMember(OBJECT_SELF))

                            {

                                GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Check 5 Pass");



                                GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Intruder = " + GN_ReturnDebugName(oIntruder));

                                if(GetObjectSeen(oIntruder))

                                {

                                    GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Shout: Determine Combat Round");

                                    GN_MyPrintString("GENERIC SHOUT DEBUG *************** Shout Clear 1800");



                                    ClearAllActions();

                                    GN_DetermineCombatRound(oIntruder);

                                }

                                else if(GetIsObjectValid(oIntruder))

                                {

                                    GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Shout: Move To Intruder");

                                    GN_MyPrintString("GENERIC SHOUT DEBUG ***************= Shout Clear 1900");

                                    ClearAllActions();

                                    float fDistance = 5.0;

                                    /*

                                    if(!GetObjectSeen(oIntruder))

                                    {

                                        fDistance = 3.0;

                                    }

                                    */

                                    //P.W. (June 8) - Put this check in to try and reduce the instances of NPCs running right up

                                    //to their enemies with blasters.

                                    if(GetDistanceBetween(OBJECT_SELF, oIntruder) < 20.0 && !GetObjectSeen(oIntruder))

                                    {

                                        ActionMoveToObject(oIntruder, TRUE, 2.0);

                                    }

                                    else

                                    {

                                        if(GN_GetWeaponType(OBJECT_SELF) == 1)

                                        {

                                            ActionMoveToObject(oIntruder, TRUE, 4.0);

                                        }

                                        else

                                        {

                                            ActionMoveToObject(oIntruder, TRUE, 15.0);

                                        }

                                    }

                                }

                                //MODIFIED by Preston Watamaniuk on May 16th

                                //Added this check to make Party Members attack after the PC engages in combat.

                                else if(IsObjectPartyMember(OBJECT_SELF))

                                {

                                    oIntruder = GetAttackTarget(oShouter);

                                    GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Attack Intruder = " + GN_ReturnDebugName(oIntruder));

                                    if(GetIsObjectValid(oIntruder))

                                    {

                                        GN_DetermineCombatRound(oIntruder);

                                    }

                                    else

                                    {

                                        oIntruder = GetSpellTarget(oShouter);

                                        GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Spell Intruder = " + GN_ReturnDebugName(oIntruder));

                                        if(GetIsObjectValid(oIntruder))

                                        {

                                            GN_DetermineCombatRound(oIntruder);

                                        }

                                    }

                                }

                            }

                            //I AM IN COMBAT

                            else if(nShoutIndex == 15 && GetIsFriend(oShouter) && oShouter != OBJECT_SELF)

                            {

                                if(GetCurrentAction(OBJECT_SELF) == ACTION_INVALID)

                                {

                                    if(GetObjectSeen(oIntruder))

                                    {

                                        GN_MyPrintString("GENERIC SHOUT DEBUG *************** Clear 2000");

                                        ClearAllActions();

                                        GN_MyPrintShoutString("GENERIC SHOUT DEBUG *************** Attack Intruder = " + GN_ReturnDebugName(oIntruder));

                                        GN_DetermineCombatRound(oIntruder);

                                        //GN_SetSpawnInCondition(SW_FLAG_SHOUTED_AT);

                                    }

                                    else if(GetIsObjectValid(oIntruder))

                                    {

                                        GN_MyPrintString("GENERIC SHOUT DEBUG *************** Clear 2100");

                                        ClearAllActions();

                                        ActionMoveToObject(oIntruder, TRUE, 5.0);

                                        //GN_SetSpawnInCondition(SW_FLAG_SHOUTED_AT);

                                    }

                                }

                            }

                        }

                    }

                }

            }

        }

        else if(GN_GetSpawnInCondition(SW_FLAG_SPECTATOR_STATE))

        {

            GN_MyPrintString("GENERIC SHOUT DEBUG *************** Clear 2200");

            ClearAllActions();

            return;

        }

    }

    /*

    if(!GN_GetSpawnInCondition(SW_FLAG_COMMONER_BEHAVIOR)

       && !GN_GetSpawnInCondition(SW_FLAG_SPECTATOR_STATE)

       && !GN_GetSpawnInCondition(SW_FLAG_AI_OFF))

    {

        if(GetPartyMemberByIndex(0) != OBJECT_SELF && nPartyAI != PARTY_AISTYLE_PASSIVE && !GetPlayerRestrictMode())

        {

            //P.W.(June 5) It looks stupid, but do not take this out.

            if(GetCurrentAction(OBJECT_SELF) == ACTION_QUEUEEMPTY && !GetUserActionsPending() && !IsObjectPartyMember(OBJECT_SELF))

            {

                if((IsObjectPartyMember(OBJECT_SELF) && IsObjectPartyMember(oShouter) && GetSoloMode() == FALSE) ||

                    !IsObjectPartyMember(OBJECT_SELF))

                {

                    GN_MyPrintString("GENERIC SHOUT DEBUG *************** Hail Mary activated by " + GN_ReturnDebugName(OBJECT_SELF));

                    GN_MyPrintString("GENERIC SHOUT DEBUG *************** Hail Mary Shout Clear 2110");

                    GN_DetermineCombatRound();

                }

            }

        }

    }

    */

    GN_MyPrintShoutString("");

}



//::///////////////////////////////////////////////

//:: SetListeningPatterns

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Sets the correct listen checks on the NPC by

    determining what talents they possess or what

    class they use.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 24, 2001

//:://////////////////////////////////////////////



void GN_SetListeningPatterns()

{

    SetListening(OBJECT_SELF, TRUE);

    SetListenPattern(OBJECT_SELF, "GEN_I_WAS_ATTACKED", 1);

    SetListenPattern(OBJECT_SELF, "GEN_I_AM_DEAD", 3);

    SetListenPattern(OBJECT_SELF, "GEN_CALL_TO_ARMS", 6);

    if(GetHasSpell(FORCE_POWER_SUPRESS_FORCE) || GetHasSpell(FORCE_POWER_FORCE_BREACH))

    {

        SetListenPattern(OBJECT_SELF, "GEN_SUPRESS_FORCE", 9);

    }

    SetListenPattern(OBJECT_SELF, "GEN_GRENADE_TOSSED", 12);

    SetListenPattern(OBJECT_SELF, "GEN_I_SEE_AN_ENEMY", 14);

    SetListenPattern(OBJECT_SELF, "GEN_COMBAT_ACTIVE", 15);



    GN_SetUpWayPoints();

    string sTag = GetTag(OBJECT_SELF);

    if(sTag != "Carth" &&

       sTag != "Bastila" &&

       sTag != "Cand" &&

       sTag != "HK47" &&

       sTag != "Jolee" &&

       sTag != "Juhani" &&

       sTag != "Mission" &&

       sTag != "T3M4" &&

       sTag != "Zaalbar" &&

       !GetIsPC(OBJECT_SELF))

    {

        DR_SpawnCreatureTreasure(OBJECT_SELF);

    }

    

    //MODIFIED by Preston Watamaniuk on May 8, 2003

    //Added functionality for dynamic or encounter creatures

    //to latch onto a Zone Controller.

    //GN_MyPrintString("ZONE DEBUG *****************" + IntToString(GetIsEncounterCreature()) + " " + GN_ReturnDebugName(OBJECT_SELF));

    if(GN_GetSpawnInCondition(SW_FLAG_DYNAMIC_COMBAT_ZONE) || GetIsEncounterCreature())

    {

        string sController;

        int nCount = 1;

        object oController, oTest;

        float fNear;

        float fClosest = 100.0;



        for(nCount; nCount < 40; nCount++)

        {

            if(nCount < 10)

            {

                sController = "ZoneController" + "0" + IntToString(nCount);

            }

            else

            {

                sController = "ZoneController" + IntToString(nCount);

            }

            oTest = GetObjectByTag(sController);

            if(GetIsObjectValid(oTest))

            {

                fNear = GetDistanceBetween(OBJECT_SELF, oTest);

                //GN_MyPrintString("ZONING DEBUG ***************** Controller Distance = " + GN_ReturnDebugName(oController) + " " + FloatToString(fNear, 4, 2));

                if(fNear < fClosest)

                {

                    fClosest = fNear;

                    oController = oTest;

                }

            }

        }

        if(GetIsObjectValid(oController) && fClosest < 30.0)

        {

            //GN_MyPrintString("ZONING DEBUG ***************** Setup Controller = " + GN_ReturnDebugName(oController));

            int nZone = StringToInt(GetStringRight(GetTag(oController), 2));

            SetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBAT_ZONE, nZone);

        }

    }

}



//::///////////////////////////////////////////////

//:: Check for Poison

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks if someone in the party is poisoned.

    If the person is a non-party NPC then they

    check if they are poisoned.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 9, 2002

//:://////////////////////////////////////////////



object GN_CheckIfPoisoned()

{

    GN_MyPrintString("GENERIC DEBUG *************** Starting Poison Check");

    effect ePoison;

    if(IsObjectPartyMember(OBJECT_SELF))

    {

        int nCnt = 0;

        for(nCnt; nCnt > 2; nCnt++)

        {

            ePoison = GetFirstEffect(GetPartyMemberByIndex(nCnt));

            while(GetIsEffectValid(ePoison))

            {

                if(GetEffectType(ePoison) == EFFECT_TYPE_POISON)

                {

                    return GetPartyMemberByIndex(nCnt);

                }

                ePoison = GetNextEffect(GetPartyMemberByIndex(nCnt));

            }

        }

    }

    else

    {

        ePoison = GetFirstEffect(OBJECT_SELF);

        while(GetIsEffectValid(ePoison))

        {

            if(GetEffectType(ePoison) == EFFECT_TYPE_POISON)

            {

                return OBJECT_SELF;

            }

            ePoison = GetNextEffect(OBJECT_SELF);

        }

    }

    GN_MyPrintString("GENERIC DEBUG ***************  Returning Invalid Poison Object");

    return OBJECT_INVALID;

}



//::///////////////////////////////////////////////

//:: Check for Injuries

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns member index +1 or false depending on

    whether the object belongs in the PCs party.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 9, 2002

//:://////////////////////////////////////////////



object GN_CheckIfInjured()

{

    GN_MyPrintString("GENERIC DEBUG ***************  Starting Injury Check Function");

    if(IsObjectPartyMember(OBJECT_SELF) || GetRacialType(OBJECT_SELF) == RACIAL_TYPE_DROID)

    {



        object oP0=GetPartyMemberByIndex(0);

        object oP1=GetPartyMemberByIndex(1);

        object oP2=GetPartyMemberByIndex(2);



        float fDown00 = 10.0;

        float fDown01 = 10.0;

        float fDown02 = 10.0;



        if(GetIsObjectValid(oP0) && GetRacialType(oP0) != RACIAL_TYPE_DROID)

        {

            fDown00 = IntToFloat(GetCurrentHitPoints(oP0)) / IntToFloat(GetMaxHitPoints(oP0));

        }

        if(GetIsObjectValid(oP1)&& GetRacialType(oP0) != RACIAL_TYPE_DROID)

        {

            fDown01 = IntToFloat(GetCurrentHitPoints(oP1)) / IntToFloat(GetMaxHitPoints(oP1));

        }

        if(GetIsObjectValid(oP2) && GetRacialType(oP0) != RACIAL_TYPE_DROID)

        {

            fDown02 = IntToFloat(GetCurrentHitPoints(oP2)) / IntToFloat(GetMaxHitPoints(oP2));

        }



        if(GetIsObjectValid(oP0) && !GetIsDead(oP0) && (fDown00 < 0.5 && fDown00 > 0.0))

        {

            GN_MyPrintString("GENERIC DEBUG ***************  Return oP0");

            return oP0;

        }

        else if(GetIsObjectValid(oP1) && !GetIsDead(oP1) && (fDown00 < 0.5 && fDown00 > 0.0))

        {

            GN_MyPrintString("GENERIC DEBUG ***************  Return oP1");

            return oP1;

        }

        else if(GetIsObjectValid(oP2) && !GetIsDead(oP2) && (fDown00 < 0.5 && fDown00 > 0.0))

        {

            GN_MyPrintString("GENERIC DEBUG ***************  Return oP2");

            return oP2;

        }

    }

    else

    {

        float fNPC = IntToFloat(GetCurrentHitPoints(OBJECT_SELF)) / IntToFloat(GetMaxHitPoints(OBJECT_SELF));

        if(fNPC < 0.5)

        {

            return OBJECT_SELF;

        }

    }

    return OBJECT_INVALID;

}



//:://///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//:: Generic Talent Routines

//:: Copyright (c) 2001 Bioware Corp.

//::////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//::////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: June 12, 2002

//::////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



int GN_TalentMasterRoutine(int nTalentConstant, object oTarget)

{

    if(GetIsObjectValid(oTarget))

    {

        talent tSpe11_01, tSpe11_02, tSpe11_03, tSpe11_04, tSpe11_05, tSpe11_06, tSpe11_07, tUse;

        int nTalent;

        int bValid = FALSE;

        int bHostile = FALSE;

        if(nTalentConstant == GEN_TALENT_SUPRESS_FORCE)

        {

            nTalent = 0xf021; //Any Area, No Harmful, Dispel, Ranged

        }

        else if(nTalentConstant == GEN_TALENT_REMOVE_POISON)

        {

            bValid = FALSE;

            tSpe11_01 = TalentSpell(FORCE_POWER_HEAL);

            tSpe11_02 = TalentSpell(FORCE_POWER_CURE);

            tSpe11_03 = TalentSpell(67); //Remove Poison Item

            if(GetCreatureHasTalent(tSpe11_01) || GetCreatureHasTalent(tSpe11_02))

            {

                bValid = TRUE;

                if(GetCreatureHasTalent(tSpe11_01))

                {

                    tUse = tSpe11_01;

                }

                else

                {

                    tUse = tSpe11_02;

                }

            }

            else if(GetCreatureHasTalent(tSpe11_03) && oTarget == OBJECT_SELF)

            {

                bValid = TRUE;

                tUse = tSpe11_03;

            }

            //nTalent = 0xff4f;

        }

        else if(nTalentConstant == GEN_TALENT_HEALING)

        {

            bValid = FALSE;

            GN_MyPrintString("GENERIC DEBUG *************** Starting Heal Talent Checks " + GN_ReturnDebugName(OBJECT_SELF));

            tSpe11_01 = TalentSpell(FORCE_POWER_HEAL);

            tSpe11_02 = TalentSpell(FORCE_POWER_CURE);



            if(GetRacialType(OBJECT_SELF) != RACIAL_TYPE_DROID)

            {

                tSpe11_05 = GetCreatureTalentBest(0x1408, 20);

            }

            else

            {

                tSpe11_05 = TalentSpell(128);

                if(!GetCreatureHasTalent(tSpe11_05))

                {

                    tSpe11_05 = TalentSpell(127);

                    if(!GetCreatureHasTalent(tSpe11_05))

                    {

                        tSpe11_05 = TalentSpell(84);

                    }

                }

            }



            tSpe11_06 = TalentSpell(FORCE_POWER_DRAIN_LIFE);

            tSpe11_07 = TalentSpell(FORCE_POWER_DEATH_FIELD);

            tUse;

            bValid = FALSE;



            if(GetCreatureHasTalent(tSpe11_01) || GetCreatureHasTalent(tSpe11_02))

            {

                GN_MyPrintString("GENERIC DEBUG *************** I have Heal or Cure");

                bValid = TRUE;

                if(GetCreatureHasTalent(tSpe11_01))

                {

                    tUse = tSpe11_01;

                }

                else

                {

                    tUse = tSpe11_02;

                }

            }

            else if(GetIsTalentValid(tSpe11_05) ||

                    GetCreatureHasTalent(tSpe11_06) ||

                    GetCreatureHasTalent(tSpe11_07))

            {

                if(oTarget == OBJECT_SELF)

                {

                    if(GetCreatureHasTalent(tSpe11_07) && !IsObjectPartyMember(OBJECT_SELF))

                    {

                        GN_MyPrintString("GENERIC DEBUG *************** I have Death Field");

                        bValid = TRUE;

                        bHostile = TRUE;

                        tUse = tSpe11_07;

                    }

                    else if(GetCreatureHasTalent(tSpe11_06) && !IsObjectPartyMember(OBJECT_SELF))

                    {

                        GN_MyPrintString("GENERIC DEBUG *************** I have Drain Life");

                        bValid = TRUE;

                        bHostile = TRUE;

                        tUse = tSpe11_06;

                    }

                    else

                    {

                        GN_MyPrintString("GENERIC DEBUG *************** I have a Med Pack");

                        bValid = TRUE;

                        tUse = tSpe11_05;

                    }

                }

            }

        }

        else if(nTalentConstant == GEN_TALENT_BUFF)

        {

            bValid = FALSE;

            tSpe11_01 = TalentSpell(36); //Master Valor

            tSpe11_02 = TalentSpell(33); //Knight Valor

            tSpe11_03 = TalentSpell(22); //Valor

            int bBuff = FALSE;

            if(GetCreatureHasTalent(tSpe11_01))

            {

                bBuff = TRUE;

                tUse = tSpe11_01;

            }

            else if(GetCreatureHasTalent(tSpe11_02))

            {

                bBuff = TRUE;

                tUse = tSpe11_02;

            }

            else if(GetCreatureHasTalent(tSpe11_03))

            {

                bBuff = TRUE;

                tUse = tSpe11_03;

            }

            GN_MyPrintString("GENERIC DEBUG *************** Spell Effect 22" + GN_ITS(GetHasSpellEffect(22)));

            GN_MyPrintString("GENERIC DEBUG *************** Spell Effect 33" + GN_ITS(GetHasSpellEffect(33)));

            GN_MyPrintString("GENERIC DEBUG *************** Spell Effect 36" + GN_ITS(GetHasSpellEffect(36)));

            if(!GetHasSpellEffect(22) &&

               !GetHasSpellEffect(33) &&

               !GetHasSpellEffect(36) &&

               bBuff == TRUE)

            {

                GN_MyPrintString("GENERIC DEBUG *************** I do have VALOR");

                bValid = TRUE;

            }

            else

            {

                GN_MyPrintString("GENERIC DEBUG *************** I do not have VALOR");

                bValid = FALSE;

            }

        }



        if(bValid == TRUE && bHostile == FALSE)

        {

            GN_MyPrintString("GENERIC DEBUG *************** Clear 2300");

            int nSpell = GetIdFromTalent(tUse);

            GN_MyPrintString("GENERIC DEBUG *************** Spells.2DA ID = " + GN_ITS(nSpell));

            ClearAllActions();

            ActionUseTalentOnObject(tUse, OBJECT_SELF);

            return TRUE;

        }

        else if(bValid == TRUE && bHostile == TRUE)

        {

            oTarget = GN_GetActivePartyMember(TRUE);

            if(GetIsObjectValid(oTarget))

            {

                GN_MyPrintString("GENERIC DEBUG *************** Hostile Heal Targeted On: " + GN_ReturnDebugName(oTarget));

                GN_MyPrintString("GENERIC DEBUG *************** Clear 2400");

                ClearAllActions();

                ActionUseTalentOnObject(tUse, oTarget);

                return TRUE;

            }

        }

        talent tUse2 = GetCreatureTalentBest(nTalent, 20);

        if(GetIsTalentValid(tUse) && !GetHasSpellEffect(GetIdFromTalent(tUse)))

        {

            if(GetIsObjectValid(oTarget))

            {

                GN_MyPrintString("GENERIC DEBUG *************** Clear 2500");

                ClearAllActions();

                GN_MyPrintString("GENERIC DEBUG *************** Target = " + GetName(oTarget) + " Talent Code = " + IntToString(nTalent));

                ActionUseTalentOnObject(tUse, OBJECT_SELF);

                return TRUE;

            }

        }

    }

    GN_MyPrintString("GENERIC DEBUG *************** " + GN_ReturnDebugName(OBJECT_SELF) + " VP = " + GN_ITS(GetCurrentHitPoints())+ "/" + GN_ITS(GetMaxHitPoints()) );

    GN_MyPrintString("GENERIC DEBUG *************** Healing Not Used");

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Last Round Setup

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Sets the following struct up so that Last Rounds

    information is easier to access.



    int nLastAction;

    int nLastActionID;

    int nLastTalentCode;

    object oLastTarget;

    int nTalentSuccessCode;

    int nIsLastTargetDebil;

    int nLastCombo;

    int nLastComboIndex;

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 26, 2002

//:://////////////////////////////////////////////



void GN_SetLastRoundData()

{

     talent tTalent;



     tPR.oLastTarget = GetLastHostileTarget();

     tPR.nIsLastTargetDebil = GetIsDebilitated(tPR.oLastTarget);

     tPR.nLastAction = GetLastAttackAction();

     if(tPR.nLastAction == ACTION_CASTSPELL)

     {

        tPR.nLastActionID = GetLastForcePowerUsed();

        tPR.nTalentSuccessCode = GetWasForcePowerSuccessful();

        tTalent = TalentSpell(tPR.nLastActionID);

        tPR.nLastTalentCode = GetCategoryFromTalent(tTalent);

     }

     else if(tPR.nLastAction == ACTION_ATTACKOBJECT)

     {

        tPR.nLastActionID = GetLastCombatFeatUsed();

        tPR.nTalentSuccessCode = GetLastAttackResult();

        tTalent = TalentFeat(tPR.nLastActionID);

        tPR.nLastTalentCode = GetCategoryFromTalent(tTalent);

     }

     //tPR.nLastCombo = GetLocalNumber(OBJECT_SELF, SW_NUMBER_LAST_COMBO);

     tPR.nLastComboIndex = GetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_INDEX);

     tPR.nCurrentCombo = GetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_ROUTINE);

}



//::///////////////////////////////////////////////

//:: Combo Sub Routine

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This function determines what move to do

    based on the last part of the combo performed.

    int nLastAction;

    int nLastActionID;

    int nLastTalentCode;

    object oLastTarget;

    int nTalentSuccessCode;

    int nIsLastTargetDebil;

    int nLastCombo;

    int nLastComboIndex;

    int nCurrentCombo;

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 27, 2002

//:://////////////////////////////////////////////

talent GN_GetComboMove(int nBoss = FALSE)

{

    int nRand;

    int nCombo;

    talent tUse;

    int nNPC_AI = GetNPCAIStyle(OBJECT_SELF); //Determines how the individual should react in combat

    GN_MyPrintString("GENERIC DEBUG *************** Starting GetComboMove");



    //Is the last combo done?

    if(tPR.nLastComboIndex == 4 || tPR.nLastComboIndex == 0)

    {

        //If so then set the local numbers controlling the combo to 0;

        SetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_INDEX, 0);

        SetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_ROUTINE, 0);

        nRand = d6();

        if(nRand > 0)//This nRand check is place here in case we need to limit combo use later

        {

            //If a Jedi use the jedi routines.

            if(GetLevelByClass(CLASS_TYPE_JEDICONSULAR) > 0 ||

               GetLevelByClass(CLASS_TYPE_JEDIGUARDIAN) > 0 ||

               GetLevelByClass(CLASS_TYPE_JEDISENTINEL) > 0)

            {

                nCombo = GN_GetStandardJediCombo(nBoss);



                GN_MyPrintString("GENERIC DEBUG *************** Starting Jedi Combo " + GN_FetchComboString(nCombo));



                SetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_INDEX, 1);

                SetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_ROUTINE, nCombo);



                return GN_GetNextTalentInCombo(nCombo);

            }

            //If a Droid use these routines

            else if(GetLevelByClass(CLASS_TYPE_COMBATDROID) > 0 ||

                    GetLevelByClass(CLASS_TYPE_EXPERTDROID) > 0)

            {

                nCombo = GN_GetStandardDroidCombo(nBoss);

                GN_MyPrintString("GENERIC DEBUG *************** Starting Droid Combo " + GN_FetchComboString(nCombo));

                SetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_INDEX, 1);

                SetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_ROUTINE, nCombo);



                return GN_GetNextTalentInCombo(nCombo);

            }

            //All others.

            else

            {

                nCombo = GN_GetStandardNPCCombo(nBoss);

                GN_MyPrintString("GENERIC DEBUG *************** Starting NPC Combo " + GN_FetchComboString(nCombo));

                SetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_INDEX, 1);

                SetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_ROUTINE, nCombo);



                return GN_GetNextTalentInCombo(nCombo);

            }

        }

        else//returning an invalid Talent here will mean action attack.

        {

            return tUse;

        }

    }

    else//if(tPR.nTalentSuccessCode > 0)

    {

        //If the PC is already in a combo then continue that combo

        GN_MyPrintString("GENERIC DEBUG *************** Continuing Combo " + GN_FetchComboString(tPR.nCurrentCombo));

        return GN_GetNextTalentInCombo(tPR.nCurrentCombo);

    }

    return tUse;

}



//::///////////////////////////////////////////////

//:: Check Droid Utility Usage

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks the target and the droid utility use

    to make sure they are compatible

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 22, 2003

//:://////////////////////////////////////////////

talent GN_CheckDroidUtilityUsage(object oTarget, talent tUse)

{

    int bSwitch;

    GN_MyPrintString("GENERIC DEBUG *************** Starting Droid Talent Double Check");

    if(GetTypeFromTalent(tUse) == TALENT_TYPE_FORCE)

    {

        GN_MyPrintString("GENERIC DEBUG *************** Droid Talent is a Spell");

        if(GetIdFromTalent(tUse) == 116 || GetIdFromTalent(tUse) == 117) //STUN RAY

        {

            if(GetRacialType(oTarget) == RACIAL_TYPE_HUMAN)

            {

                return tUse;

            }

            else

            {

                bSwitch = TRUE;

            }

        }

        if(GetIdFromTalent(tUse) == 118 || GetIdFromTalent(tUse) == 119) //SHIELD DISRUPTOR

        {

            if(GetHasSpellEffect(99, oTarget) || GetHasSpellEffect(100, oTarget) || GetHasSpellEffect(101, oTarget) ||

               GetHasSpellEffect(102, oTarget) || GetHasSpellEffect(103, oTarget) || GetHasSpellEffect(104, oTarget) ||

               GetHasSpellEffect(105, oTarget) || GetHasSpellEffect(106, oTarget) || GetHasSpellEffect(107, oTarget) ||

               GetHasSpellEffect(110, oTarget) || GetHasSpellEffect(111, oTarget) || GetHasSpellEffect(112, oTarget) ||

               GetHasSpellEffect(113, oTarget) || GetHasSpellEffect(114, oTarget) || GetHasSpellEffect(115, oTarget))

            {

                return tUse;

            }

            else

            {

                bSwitch = TRUE;

            }

        }

    }

    if(bSwitch == TRUE)

    {

        talent tFeat = GetCreatureTalentBest(0x1181, 20);

        if(GetIsTalentValid(tUse) && GetCreatureHasTalent(tUse))

        {

            return tFeat;

        }

        else

        {

            talent Invalid;

            return Invalid;

        }

    }

    return tUse;

}



//::///////////////////////////////////////////////

//:: Throw Lightsaber Check

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks the target and the force power to make

    sure that a lightsaber is not thrown from close

    range.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 24, 2003

//:://////////////////////////////////////////////

talent GN_CheckThrowLightSaberUsage(object oTarget, talent tUse)

{

    int bSwitch = FALSE;

    if(GetTypeFromTalent(tUse) == TALENT_TYPE_FORCE)

    {

        if(GetIdFromTalent(tUse) == FORCE_POWER_LIGHT_SABER_THROW || GetIdFromTalent(tUse) == FORCE_POWER_LIGHT_SABER_THROW_ADVANCED)

        {

            GN_MyPrintString("GENERIC DEBUG *************** Lightsaber Throw Check = " + FloatToString(GetDistanceBetween(OBJECT_SELF, oTarget),4,2));

            if(GetDistanceBetween(OBJECT_SELF, oTarget) < 10.0)

            {

                bSwitch = TRUE;

            }

        }

    }

    if(bSwitch == TRUE)

    {

        talent tFeat = GetCreatureTalentBest(0x1104, 20);

        if(GetIsTalentValid(tUse) && GetCreatureHasTalent(tUse))

        {

            return tFeat;

        }

        else

        {

            talent Invalid;

            return Invalid;

        }

    }

    return tUse;

}



//::///////////////////////////////////////////////

//:: Check Droid Force Power Usage

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks the force power and makes sure it can

    be used on a droid.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On:May 12, 2003

//:://////////////////////////////////////////////

talent GN_CheckNonDroidForcePower(object oTarget, talent tUse)

{

    int bSwitch = FALSE;

    if(GetTypeFromTalent(tUse) == TALENT_TYPE_FORCE)

    {

        if(GetIdFromTalent(tUse) == FORCE_POWER_HOLD ||

           GetIdFromTalent(tUse) == FORCE_POWER_HORROR ||

           GetIdFromTalent(tUse) == FORCE_POWER_INSANITY ||

           GetIdFromTalent(tUse) == FORCE_POWER_KILL ||

           GetIdFromTalent(tUse) == FORCE_POWER_PLAGUE ||

           GetIdFromTalent(tUse) == FORCE_POWER_SLEEP ||

           GetIdFromTalent(tUse) == FORCE_POWER_SLOW ||

           GetIdFromTalent(tUse) == FORCE_POWER_STUN ||

           GetIdFromTalent(tUse) == FORCE_POWER_WOUND ||

           GetIdFromTalent(tUse) == FORCE_POWER_AFFLICTION ||

           GetIdFromTalent(tUse) == FORCE_POWER_CHOKE ||

           GetIdFromTalent(tUse) == FORCE_POWER_DEATH_FIELD ||

           GetIdFromTalent(tUse) == FORCE_POWER_DRAIN_LIFE ||

           GetIdFromTalent(tUse) == FORCE_POWER_FEAR)

        {

            if(GetRacialType(oTarget) == RACIAL_TYPE_DROID)

            {

                bSwitch = TRUE;

            }

        }

    }

    if(bSwitch == TRUE)

    {

        talent tFeat = GetCreatureTalentBest(0x1104, 20);

        if(GetIsTalentValid(tUse) && GetCreatureHasTalent(tUse))

        {

            return tFeat;

        }

        else

        {

            talent Invalid;

            return Invalid;

        }

    }

    return tUse;

}



//::///////////////////////////////////////////////

//:: Play Ambient Animations

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Play the correct animations based on the

    spawn in condition selected.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 4, 2002

//:://////////////////////////////////////////////



void GN_PlayAmbientAnimation()

{

    if(!GetIsInConversation(OBJECT_SELF))

    {

        location lLocal;

        vector vFrnd;

        int nRoll = d2();

        object oFriend = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_FRIEND, OBJECT_SELF, nRoll, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

        if(!GetIsObjectValid(oFriend))

        {

            oFriend = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_NEUTRAL, OBJECT_SELF, nRoll, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

        }

        object oEnemy = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY);

        int nHDMe = GetHitDice(OBJECT_SELF);

        int nHDOther = GetHitDice(oFriend);



        if(!GN_CheckShouldFlee() || !GN_GetSpawnInCondition(SW_FLAG_COMMONER_BEHAVIOR))

        {

            if(GN_GetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS))

            {

                vFrnd = GetPosition(oFriend);

                nRoll = d6();

                if(GetIsObjectValid(oFriend) && GetDistanceBetween(oFriend, OBJECT_SELF) < 5.0 && !IsObjectPartyMember(oFriend))

                {

                    SetFacingPoint(vFrnd);

                    GN_MyPrintString("GENERIC DEBUG *************** Clear 2600");

                    ClearAllActions();

                    if(nRoll == 1 || nRoll == 2)

                    {

                        ActionPlayAnimation(ANIMATION_LOOPING_TALK_NORMAL, 1.0, 3.0);

                    }

                    else if(nRoll == 3)

                    {

                        ActionPlayAnimation(ANIMATION_LOOPING_TALK_LAUGHING, 1.0, 3.0);

                    }

                    else if(nRoll == 4)

                    {

                        ActionPlayAnimation(ANIMATION_LOOPING_TALK_FORCEFUL, 1.0, 3.0);

                    }

                    else if(nRoll == 5)

                    {

                        ActionPlayAnimation(ANIMATION_FIREFORGET_HEAD_TURN_LEFT);

                    }

                    else if(nRoll == 6)

                    {

                        ActionPlayAnimation(ANIMATION_FIREFORGET_HEAD_TURN_RIGHT);

                    }

                }

                else

                {

                    nRoll = d8();

                    if(nRoll == 1)

                    {

                        ActionPlayAnimation(ANIMATION_FIREFORGET_PAUSE_BORED, 1.0);

                    }

                    else if(nRoll == 2)

                    {

                        ActionPlayAnimation(ANIMATION_FIREFORGET_PAUSE_SCRATCH_HEAD, 1.0);

                    }

                    else if(nRoll == 3)

                    {

                        ActionPlayAnimation(ANIMATION_LOOPING_PAUSE2, 1.0, 3.0);

                    }

                    else if(nRoll == 4 || nRoll == 5)

                    {

                        if(GetGender(OBJECT_SELF) == GENDER_MALE)

                        {

                            GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, FALSE);

                            ActionPlayAnimation(ANIMATION_LOOPING_PAUSE3, 1.0, 20.4);

                            ActionDoCommand(GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, TRUE));

                        }

                        else if(GetGender(OBJECT_SELF) == GENDER_FEMALE)

                        {

                            GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, FALSE);

                            ActionPlayAnimation(ANIMATION_LOOPING_PAUSE3, 1.0, 13.3);

                            ActionDoCommand(GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, TRUE));

                        }

                    }

                    else if(nRoll == 6)

                    {

                        ActionPlayAnimation(ANIMATION_FIREFORGET_HEAD_TURN_LEFT);

                    }

                    else if(nRoll == 7)

                    {

                        ActionPlayAnimation(ANIMATION_FIREFORGET_HEAD_TURN_RIGHT);

                    }

                    else if(nRoll == 8)

                    {

                        GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, FALSE);

                        ActionPlayAnimation(ANIMATION_LOOPING_PAUSE2, 1.0, 5.0);

                        ActionDoCommand(GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, TRUE));

                    }

                }

            }

            else if(GN_GetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS_MOBILE))

            {

                nRoll = d8();

                GN_MyPrintString("GENERIC DEBUG *************** Clear 2700");

                ClearAllActions();

                if(nRoll == 1)

                {

                    ActionPlayAnimation(ANIMATION_LOOPING_PAUSE2, 1.0, 2.0);

                }

                else if(nRoll == 2)

                {

                    ActionPlayAnimation(ANIMATION_FIREFORGET_TAUNT, 1.0);

                }

                else if(nRoll == 3)

                {

                    //ActionPlayAnimation(ANIMATION_FIREFORGET_HEAD_TURN_LEFT, 0.75);

                    //ActionPlayAnimation(ANIMATION_FIREFORGET_HEAD_TURN_RIGHT, 0.75);

                }

                else if(nRoll == 4)

                {

                    ActionPlayAnimation(ANIMATION_FIREFORGET_VICTORY1, 1.0);

                }

                else if(nRoll >= 5)

                {

                    ActionRandomWalk();

                }

            }

        }

        else if(GN_CheckShouldFlee() && GN_GetSpawnInCondition(SW_FLAG_COMMONER_BEHAVIOR))

        {

            GN_CommonAI();

        }

    }

}

//::///////////////////////////////////////////////

//:: Commoner AI

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    If ever engaged in combat they will flee.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: July 18, 2002

//:://////////////////////////////////////////////

int GN_CommonAI()

{

    GN_MyPrintString("GENERIC DEBUG *************** Start Commoner AI");

    object oEnemy = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY);

    object oFlee;

    int bValid = TRUE;

    int nIdx = 1;



    object oNeutral = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_NEUTRAL);

    while(GetIsObjectValid(oNeutral) && bValid == TRUE)

    {

        if(GetStandardFaction(oNeutral) == STANDARD_FACTION_HOSTILE_1 ||

            GetStandardFaction(oNeutral) == STANDARD_FACTION_HOSTILE_2 ||

            GetStandardFaction(oNeutral) == STANDARD_FACTION_INSANE)

        {

            if(GetDistanceBetween(OBJECT_SELF, oNeutral) <= 20.0)

            {

                oFlee = oNeutral;

                bValid = FALSE;

            }

        }

        else

        {

            nIdx++;

            oNeutral = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_NEUTRAL, OBJECT_SELF, nIdx);

        }

    }



    if(GetIsObjectValid(oEnemy))

    {

        GN_MyPrintString("GENERIC DEBUG *************** Clear 2710");

        ClearAllActions();

        ActionMoveAwayFromObject(oEnemy, TRUE, 20.0);

        DelayCommand(0.2, ActionDoCommand(GN_ActionDoPostDCRChecks()));

        return TRUE;

    }

    else if(GetIsObjectValid(oFlee))

    {

        GN_MyPrintString("GENERIC DEBUG *************** Object Flee = " + GN_ReturnDebugName(oFlee));

        GN_MyPrintString("GENERIC DEBUG *************** Clear 2720");

        ClearAllActions();

        ActionMoveAwayFromObject(oFlee, TRUE, 20.0);

        DelayCommand(0.2, ActionDoCommand(GN_ActionDoPostDCRChecks()));

        return TRUE;

    }

    return FALSE;

}

//::///////////////////////////////////////////////

//:: Should Commoner Flee

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks a number of conditions for a commoner

    to flee.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 20, 2002

//:://////////////////////////////////////////////



int GN_CheckShouldFlee()

{

    int nIdx = 1;

    object oNeutral = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_NEUTRAL, OBJECT_SELF, 1, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

    object oHostile = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF, 1, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

    while(GetIsObjectValid(oNeutral) || GetIsObjectValid(oHostile))

    {

        if(GetIsObjectValid(oHostile))

        {

            return TRUE;

        }

        if(GetIsObjectValid(oNeutral))

        {

            if(GetStandardFaction(oNeutral) == STANDARD_FACTION_HOSTILE_1 ||

                GetStandardFaction(oNeutral) == STANDARD_FACTION_HOSTILE_2 ||

                GetStandardFaction(oNeutral) == STANDARD_FACTION_INSANE)

            {

                return TRUE;

            }

        }

        nIdx++;

        oNeutral = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_NEUTRAL, OBJECT_SELF, nIdx, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Reset Deactivated Droid

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Resets a Droid to his deactivated animation

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 25, 2003

//:://////////////////////////////////////////////



void GN_ResetDroidDeactivationState(object oDroid = OBJECT_SELF)

{

    /*

    GN_SetSpawnInCondition(SW_FLAG_EVENT_ON_HEARTBEAT, FALSE);

    ClearAllActions();

    ActionPlayAnimation(ANIMATION_LOOPING_DEACTIVATE, 1.0, 900.0);

    ActionDoCommand(GN_SetSpawnInCondition(SW_FLAG_EVENT_ON_HEARTBEAT, TRUE));

    */

    ClearAllActions();

    ActionPlayAnimation(ANIMATION_LOOPING_DEACTIVATE, 1.0, -1.0);

    GN_SetSpawnInCondition(SW_FLAG_EVENT_ON_HEARTBEAT, FALSE);

}



//::///////////////////////////////////////////////

//:: Determine Attack Target

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks the nearest seen target and oIntruder

    for a valid attack target.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 7, 2002

//:://////////////////////////////////////////////

object GN_DetermineAttackTarget(object oIntruder = OBJECT_INVALID)

{

    GN_MyPrintString("GENERIC DEBUG *************** Starting: Determine Attack Target");



    int nPartyAI = GetPartyAIStyle();

    int nNPC_AI = GetNPCAIStyle(OBJECT_SELF);

    object oTarget;

    object oLastTarget = GetLastHostileTarget();



    GN_MyPrintString("GENERIC DEBUG *************** Intruder = " + IntToString(GetIsObjectValid(oIntruder)) + " Last Target = " + IntToString(GetIsObjectValid(oLastTarget)));



    if(GetIsObjectValid(oIntruder) && !GetIsDead(oIntruder) && !GetIsDebilitated(oIntruder))

    {

        GN_MyPrintString("GENERIC DEBUG *************** Intruder Target Returned = " + ObjectToString(oIntruder));

        return oIntruder;

    }

    else if(GetIsObjectValid(oLastTarget) && !GetIsDead(oLastTarget) && !GetIsDebilitated(oLastTarget))

    {

        GN_MyPrintString("GENERIC DEBUG *************** Last Target Returned = " + ObjectToString(oIntruder));

        return oLastTarget;

    }

    else

    {

        if(nPartyAI == PARTY_AISTYLE_AGGRESSIVE)

        {

            int nCnt = 1;

            GN_MyPrintString("GENERIC DEBUG *************** Getting nearest target - 249");

            object oATarget = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF, nCnt, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

            oTarget = oATarget;

            while(!GetIsDebilitated(oTarget) && GetIsObjectValid(oTarget))

            {

                nCnt++;

                oTarget = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF, nCnt, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

            }

            if(!GetIsObjectValid(oTarget) && GetIsObjectValid(oATarget))

            {

                oTarget = oATarget;

            }

        }

        else if(nPartyAI == PARTY_AISTYLE_DEFENSIVE)

        {

            int nCnt = 0;

            object oHostile;

            while(!GetIsObjectValid(oHostile) && nCnt < 3)

            {

                oHostile = GetLastHostileActor(GetPartyMemberByIndex(nCnt));

                nCnt++;

            }

            if(GetIsObjectValid(oHostile))

            {

                GN_MyPrintString("GENERIC DEBUG *************** Getting nearest target - 262");

                oTarget = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF, 1, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

            }

            else

            {

                oHostile = GetLastHostileTarget(GetPartyMemberByIndex(0));

                if(GetIsObjectValid(oHostile))

                {

                    GN_MyPrintString("GENERIC DEBUG *************** Getting nearest target - 269");

                    oTarget = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF, 1, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

                }

            }

        }

        else if(nPartyAI != PARTY_AISTYLE_PASSIVE)

        {

            GN_MyPrintString("GENERIC DEBUG *************** Getting nearest target - 275");

            oTarget = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF, 1, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

        }

        else

        {

            GN_MyPrintString("GENERIC DEBUG *************** Getting nearest target - 279");

            oTarget = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF, 1, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN);

        }

    }

    if(GetIsObjectValid(oTarget))

    {

        GN_MyPrintString("GENERIC DEBUG *************** Attack Target From Determine Attack Target = " + GN_ReturnDebugName(oTarget));

        return oTarget;

    }

    GN_MyPrintString("GENERIC DEBUG *************** No Attack Targets Found");

    return OBJECT_INVALID;

}



//::///////////////////////////////////////////////

//:: Return Talent Code

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This function determines the state of the selected

    attack target and what should be done to them.

    If the target is last rounds target then they

    will try not to use failed attack types.



    NOTE: The functionality for area attacks and

    specialized talent use will be coded here.

    For the time being, I will just try to get

    the appropriate cascade of talents being used.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 14, 2002

//:://////////////////////////////////////////////



int GN_GetAttackTalentCode(object oTarget)

{

    GN_MyPrintString("GENERIC DEBUG *************** Starting: Getting Talent Attack Code");



    int nPreviousTalentCode;

    //GN_MyPrintString("GENERIC DEBUG *************** Cooked Return Code  0x0100");



    GN_MyPrintString("GENERIC DEBUG *************** Debilitated = " + IntToString(GetIsDebilitated(oTarget)));



    if(!GetIsDead(oTarget) && GetIsObjectValid(oTarget) && !GetIsDebilitated(oTarget) && GetLastHostileTarget() == oTarget)

    {

        //GN_MyPrintString("GENERIC DEBUG *************** Talent Code: Before GetPreviousTalent");

        nPreviousTalentCode = GN_GetPreviousTalentCode();

        //GN_MyPrintString("GENERIC DEBUG *************** Talent Code: Before If Compare");

        if(GN_CompareTalents(nPreviousTalentCode, 0xf2ff))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Talent Code: 0xff1f");

            if(GN_GetHasViableTalent(0xff1f))

            {

                GN_MyPrintString("GENERIC DEBUG *************** Return Code 0xff1f");

                return 0xff1f;

            }

            if(GN_GetHasViableTalent(0x0100))

            {

                GN_MyPrintString("GENERIC DEBUG *************** Return Code  0xf1ff");

                return 0xf1ff;

            }

        }

        else if(GN_CompareTalents(nPreviousTalentCode, 0xff1f))

        {

            if(GN_GetHasViableTalent(0xf1f0))

            {

                GN_MyPrintString("GENERIC DEBUG *************** Return Code  0xf1ff");

                return 0xf1ff;

            }

        }

    }

    else if(!GetIsDead(oTarget) && GetIsObjectValid(oTarget) && !GetIsDebilitated(oTarget) && GetLastHostileTarget() != oTarget)

    {

        if(GN_GetHasViableTalent(0xf3ff))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Return Code  0xf3ff");

            return 0xf3ff;

        }

        if(GN_GetHasViableTalent(0xf2ff))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Return Code  0xf2ff");

            return 0xf2ff;

        }

        if(GN_GetHasViableTalent(0xff1f))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Return Code  0xff1f");

            return 0xff1f;

        }

        if(GN_GetHasViableTalent(0xf1ff))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Return Code  0xf1ff");

            return 0xf1ff;

        }

    }

    else if(!GetIsDead(oTarget) && GetIsObjectValid(oTarget) && GetIsDebilitated(oTarget))

    {

        if(GN_GetHasViableTalent(0xf1ff))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Return Code  0xf1ff");

            return 0xf1ff;

        }

    }

    GN_MyPrintString("GENERIC DEBUG *************** Return Code  0xffff");

    return 0xffff;

}



//this function was cut from the generics but is needed

//here to keep scripts from breaking.

void GN_SetDayNightPresence(int nPresenceSetting)

{



}

''',

    'k_inc_gensupport': b'''//:: k_inc_gensupport

/*

    v1.0

    Support Include for k_inc_generic



    NOTE - To get these functions

    use k_inc_generic

*/

//:: Created By: Preston Watamaniuk

//:: Copyright (c) 2002 Bioware Corp.



//BOSS ATTACK TYPES

int SW_BOSS_ATTACK_TYPE_GRENADE = 1;

int SW_BOSS_ATTACK_TYPE_FORCE_POWER = 2;

int SW_BOSS_ATTACK_TYPE_NPC = 3;

int SW_BOSS_ATTACK_TYPE_PC = 4;

int SW_BOSS_ATTACK_ANY = 5;

int SW_BOSS_ATTACK_DROID = 6;



//LOCAL NUMBERS

int SW_NUMBER_COMBO_ROUTINE = 3;

int SW_NUMBER_COMBO_INDEX = 4;

int SW_NUMBER_LAST_COMBO = 5;

int SW_NUMBER_ROUND_COUNTER = 6;

int SW_NUMBER_COMBAT_ZONE = 7;



//COMBO CONSTANTS

int SW_COMBO_RANGED_FEROCIOUS = 1;

int SW_COMBO_RANGED_AGGRESSIVE = 2;

int SW_COMBO_RANGED_DISCIPLINED = 3;

int SW_COMBO_RANGED_CAUTIOUS = 4;

int SW_COMBO_MELEE_FEROCIOUS = 5;

int SW_COMBO_MELEE_AGGRESSIVE = 6;

int SW_COMBO_MELEE_DISCIPLINED = 7;

int SW_COMBO_MELEE_CAUTIOUS = 8;

int SW_COMBO_BUFF_PARTY = 9;

int SW_COMBO_BUFF_DEBILITATE = 10;

int SW_COMBO_BUFF_DAMAGE = 11;

int SW_COMBO_BUFF_DEBILITATE_DESTROY = 12;

int SW_COMBO_SUPRESS_DEBILITATE_DESTROY = 13;

int SW_COMBO_SITH_ATTACK = 14;

int SW_COMBO_BUFF_ATTACK = 15;

int SW_COMBO_SITH_CONFOUND = 16;

int SW_COMBO_JEDI_SMITE = 17;

int SW_COMBO_SITH_TAUNT = 18;

int SW_COMBO_SITH_BLADE = 19;

int SW_COMBO_SITH_CRUSH = 20;

int SW_COMBO_JEDI_CRUSH = 21;

int SW_COMBO_SITH_BRUTALIZE = 22;

int SW_COMBO_SITH_DRAIN = 23;

int SW_COMBO_SITH_ESCAPE = 24;

int SW_COMBO_JEDI_BLITZ = 25;

int SW_COMBO_SITH_SPIKE = 26;

int SW_COMBO_SITH_SCYTHE = 27;

int SW_COMBO_DROID_UTILITIES = 28;

int SW_COMBO_DROID_UTILITIES_2 = 29;

int SW_COMBO_INVALID = 30;



int SW_FLAG_TARGET_FRIEND = 59;



//****SUPPORT FUNCTIONS FOR THE GENERICS**************************************************************************

//Returns the number targets attacking the passed in object

int GN_GetAttackers(object oTarget);

//Returns the index of the party member passed in or false if the object is not a party member.

int GN_CheckNPCIsInParty(object oNPC);

//Checks whether the attempted spell or attack targets are true

int GN_CheckAttemptedSpellAttackTarget();

//Determines if the object has a valid attempted spell or attack target or a valid attack target.

int GN_GetIsFighting(object oFighting);

//Compares to talent codes to see if specific bits are true.

int GN_CompareTalents(int nTalent1, int nTalent2);

// Returns the talent code for the previous round.

int GN_GetPreviousTalentCode();

//Takes a spell constant and passes back the code

int GN_GetSpellTalentCode(int nSpell);

//Takes a feat constant and passes back the code

int GN_GetFeatTalentCode(int nFeat);

//Searchs for viable talents that can be used by the user and passes back yes or no according to whether one is found.

int GN_GetHasViableTalent(int nTalentCode);

//Returns the exclusion code for the talent based on the racial type of the creature passed in.

int GN_GetExclusionCode(object oTarget);

//This takes a combo constant and returns a talent.

talent GN_GetNextTalentInCombo(int nCombo);

//Determines if a combo is valid for the object in question

int GN_GetIsComboValid(int nComboType);

//Does the Jedi have a damaging Force Power

int GN_GetHasDamagingForcePower();

//Gets a random combo for a default AI Jedi

int GN_GetStandardJediCombo(int nBoss = FALSE);

//Gets a random combo for a default AI Droid

int GN_GetStandardDroidCombo(int nBoss = FALSE);

//Gets a random combo for a default AI NPC

int GN_GetStandardNPCCombo(int nBoss = FALSE);

// Returns 2 for Ranged and 1 for Melee weapons, checking the basetype

int GN_GetWeaponType(object oTarget = OBJECT_SELF);

//Gets the NPC to eqyuip a melee = 1 or ranged = 2 weapon.

int GN_EquipAppropriateWeapon();

//Returns a talent for the boss to perform in combat.

talent GN_GetBossCombatMove(int nBossAttackType, int nDroid = FALSE);

//Get Boss AOE Force Powers

talent GN_GetAOEForcePower(int nDroid = FALSE);

//Get Boss Single Target Force Powers

talent GN_GetTargetedForcePower(int nDroid = FALSE);

//Returns the number of party members who are active

int GN_GetActivePartyMemberCount();

//Returns the active party member who is not Member(0)

object GN_GetActivePartyMember(int nDrainTarget = FALSE);

//This function returns an active party member. They must not be dead.  The debilitated parameter will

//ignore those party members already debilitated.

object GN_ReturnActivePartyMember(int nDebil = FALSE);



//****VERIFICATION FOR COMMANDS FOR COMBOS**************************************************************************



//Check Push Series

int GN_CheckSeriesForcePush();

//Check Armor Series

int GN_CheckSeriesArmor();

//Check Fear Series

int GN_CheckSeriesFear();

//Check Hold Series

int GN_CheckSeriesHold();

//Check Poison Series

int GN_CheckSeriesAfflict();

//Check Saber Throw Series

int GN_CheckSeriesSaberThrow();

//Check Lightning Series

int GN_CheckSeriesLightning();

//Check Jump Series

int GN_CheckSeriesJump();

//Check Choke Series

int GN_CheckSeriesChoke();

//Check Drain Life Series

int GN_CheckSeriesDrainLife();

//Check Speed Series

int GN_CheckSeriesSpeed();

//Checks if the droid has utility items

int GN_CheckSeriesDroidUtilities();

//Checks Mind Series

int GN_CheckSeriesMind();

//Checks Resist Series

int GN_CheckSeriesResist();

//Checks Force Immunity Series();

int GN_CheckSeriesForceImmunity();

//Checks the Breach Series

int GN_CheckSeriesBreach();



//****GET COMMANDS FOR COMBOS**************************************************************************



//Fetch Series Force Push Power

int GN_GetSeriesForcePush();

//Fetch Series Force Armor Power

int GN_GetSeriesForceArmor();

//Fetch Series Fear Power

int GN_GetSeriesFear();

//Fetch Series Hold Power

int GN_GetSeriesHold();

//Fetch Series Afflict Power

int GN_GetSeriesAfflict();

//Fetch Series Saber Throw Power

int GN_GetSeriesSaberThrow();

//Fetch Series Lightning Power

int GN_GetSeriesLightning();

//Fetch Series Jump Power

int GN_GetSeriesJump();

//Fetch Series Choke Power

int GN_GetSeriesChoke();

//Fetch Series Drain Life Power

int GN_GetSeriesDrainLife();

//Fetch Series Speed Power

int GN_GetSeriesSpeed();

//Fetch Melee Feat

int GN_GetSeriesMeleeFeat();

//Fetch Ranged Feat

int GN_GetSeriesRangedFeat();

//Fetch Mind Series

int GN_GetSeriesMind();

//Fetch Resist Series

int GN_GetSeriesResist();

//Fetch Force Immunity Series();

int GN_GetSeriesForceImmunity();

//Fetch the Breach Series

int GN_GetSeriesBreach();



//****DEBUG COMMANDS FOR THE GENERICS**************************************************************************



//Basically, a wrapper for AurPostString

void GN_PostString(string sString = "",int x = 10,int y = 10,float fShow = 4.0);

//Makes the object running the script say a speak string.

void GN_MySpeakString(string sString);

//Makes the nearest PC say a speakstring.

void GN_AssignPCDebugString(string sString);

//Inserts a print string into the log file for debugging purposes.

void GN_MyPrintString(string sString);

//Prints to the log file the shout received by a target.

void GN_PrintShoutType(object oShouter, int nShout);

//Returns the object ID and name appended to each other.

string GN_ReturnDebugName(object oTarget);

//Returns a string of the combo being used.

string GN_FetchComboString(int nCombo);

//Checks the friendly fire on the target out to 3.5m by default.

int GN_CheckFriendlyFireOnTarget(object oTarget, float fDistance = 4.0);

//Checks the enemies around a target object.

int GN_CheckEnemyGroupingOnTarget(object oTarget, float fDistance = 4.0);

//Searches the area and marks a group as a viable target for a grenade

object GN_FindGrenadeTarget();

//Searches the area and marks a group as a viable target for a AOE force power

object GN_FindAOETarget();

//Returns a grenade appropriate to the target

talent GN_GetGrenadeTalent(int nDroid = FALSE);

//Returns the AI style in a string

string GN_ReturnAIStyle(object oTarget = OBJECT_SELF);

//Prints a string from a int

string GN_ITS(int sFutureString);

//These debug commands are used for debugging shouts only

void GN_PostShoutString(string sString = "",int x = 10,int y = 10,float fShow = 4.0);

//These debug commands are used for debugging shouts o

void GN_MyPrintShoutString(string sString);





//::///////////////////////////////////////////////

//:: Get Attackers

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns the number objects attacking the object;

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 9, 2002

//:://////////////////////////////////////////////



int GN_GetAttackers(object oTarget)

{

    int nCnt = 0;

    object oAttacker = GetFirstAttacker(oTarget);

    while(GetIsObjectValid(oAttacker))

    {

        nCnt++;

        oAttacker = GetNextAttacker(oTarget);

    }

    return nCnt;

}



//::///////////////////////////////////////////////

//:: Am I a party member

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns member index +1 or false depending on

    whether the object belongs in the PCs party.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 9, 2002

//:://////////////////////////////////////////////



int GN_CheckNPCIsInParty(object oNPC)

{

    if(GetPartyMemberByIndex(0) == oNPC)

    {

        return 1;

    }

    else if(GetPartyMemberByIndex(1) == oNPC)

    {

        return 2;

    }

    else if(GetPartyMemberByIndex(2) == oNPC)

    {

        return 3;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: GetAttempted Spell or Attack Target State

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns true if the spell or attack target is

    true

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 8, 2002

//:://////////////////////////////////////////////



int GN_CheckAttemptedSpellAttackTarget()

{

    object oAttack = GetAttemptedAttackTarget();

    object oSpell = GetAttemptedSpellTarget();

    if(GetIsObjectValid(oAttack) || GetIsObjectValid(oSpell))

    {

        return TRUE;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: GetIsFighting

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks if the passed object has an Attempted

    Attack or Spell Target

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: July 16, 2002

//:://////////////////////////////////////////////

int GN_GetIsFighting(object oFighting)

{

    object oAttack = GetAttemptedAttackTarget();

    object oSpellTarget = GetAttemptedSpellTarget();

    object oAttacking = GetAttackTarget();

    object oMove = GetAttemptedMovementTarget();



    if(GetTag(OBJECT_SELF) == "DEBUG")

    {

        GN_ReturnDebugName(OBJECT_SELF);

        GN_PostString("Attempted Attack Target = " + IntToString(GetIsObjectValid(oAttack)), 10,20, 4.0);

        GN_PostString("Attempted Spell Target = " + IntToString(GetIsObjectValid(oSpellTarget)), 10,22, 4.0);

        GN_PostString("Attack Target = " + IntToString(GetIsObjectValid(oAttacking)), 10,24, 4.0);

        GN_PostString("Move Target = " + IntToString(GetIsObjectValid(oMove)), 10,26, 4.0);

    }



    if(GetIsObjectValid(oAttack) || GetIsObjectValid(oSpellTarget) || GetIsObjectValid(oAttacking) ||

     (GetIsObjectValid(oMove) && GetIsEnemy(oMove)))

    {

        return TRUE;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Compare Talents

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks the bits of Talent 1 against the bits

    of Talent 2 to see if 1 is true.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 12, 2002

//:://////////////////////////////////////////////



int GN_CompareTalents(int nTalent1, int nTalent2)

{

    if(nTalent1 & nTalent2)

    {

        //GN_MyPrintString("GENERIC DEBUG *************** Comparison of " + IntToString(nTalent1) + " / " + IntToString(nTalent2));

        return TRUE;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Get Last Talent Code

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Determines the last talent that was used

    by OBJECT_SELF

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 14, 2002

//:://////////////////////////////////////////////



int GN_GetPreviousTalentCode()

{

    int nAction = GetLastAttackAction();

    int nFeatSpell;

    if(nAction == ACTION_CASTSPELL)

    {

        nFeatSpell = GetLastForcePowerUsed();

        nFeatSpell = GN_GetSpellTalentCode(nFeatSpell);

    }

    else if(nAction == ACTION_ATTACKOBJECT)

    {

        nFeatSpell = GetLastCombatFeatUsed();

        nFeatSpell = GN_GetFeatTalentCode(nFeatSpell);

    }

    return nFeatSpell;

}



//::///////////////////////////////////////////////

//:: Get Spell Talent Code

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns the talent code for a particular spell

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 14, 2002

//:://////////////////////////////////////////////



int GN_GetSpellTalentCode(int nSpell)

{

    talent tSpell = TalentSpell(nSpell);

    return GetCategoryFromTalent(tSpell);

}



//::///////////////////////////////////////////////

//:: Get Feat Talent Code

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns the talent code for a particular feat

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 14, 2002

//:://////////////////////////////////////////////



int GN_GetFeatTalentCode(int nFeat)

{

    talent tFeat = TalentSpell(nFeat);

    return GetCategoryFromTalent(tFeat);

}



//::///////////////////////////////////////////////

//:: Get Has Viable Talent

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Takes a talent code and searches for a viable

    talent from the bunch

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 14, 2002

//:://////////////////////////////////////////////



int GN_GetHasViableTalent(int nTalentCode)

{

    talent tTest = GetCreatureTalentBest(nTalentCode, 20);

    if(GetIsTalentValid(tTest))

    {

        return TRUE;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Get Exclusion Code

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns an exclusion code based on the Racial

    Type of the target

    0x00 = None

    0x01 = Organic

    0x02 = Droid

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 14, 2002

//:://////////////////////////////////////////////



int GN_GetExclusionCode(object oTarget)

{

    int nRacial = GetRacialType(oTarget);

    if(nRacial == RACIAL_TYPE_DROID)

    {

        //GN_MyPrintString("GENERIC DEBUG *************** Exclusion Used: 0x01");

        return 0x01;

    }

    else if(nRacial == RACIAL_TYPE_HUMAN)

    {

        //GN_MyPrintString("GENERIC DEBUG *************** Exclusion Used: 0x02");

        return 0x02;

    }

    //GN_MyPrintString("GENERIC DEBUG *************** Exclusion Used: 0x03");

    return 0x03;

}



//::///////////////////////////////////////////////

//:: Get Jedi Combo

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns a proper Jedi Combo for Standard AI



int SW_COMBO_RANGED_FEROCIOUS = 1;

int SW_COMBO_RANGED_AGGRESSIVE = 2;

int SW_COMBO_RANGED_DISCIPLINED = 3;

int SW_COMBO_RANGED_CAUTIOUS = 4;

int SW_COMBO_MELEE_FEROCIOUS = 5;

int SW_COMBO_MELEE_AGGRESSIVE = 6;

int SW_COMBO_MELEE_DISCIPLINED = 7;

int SW_COMBO_MELEE_CAUTIOUS = 8;

int SW_COMBO_BUFF_PARTY = 9;

int SW_COMBO_BUFF_DEBILITATE = 10;

int SW_COMBO_BUFF_DAMAGE = 11;

int SW_COMBO_BUFF_DEBILITATE_DESTROY = 12;

int SW_COMBO_SUPRESS_DEBILITATE_DESTROY = 13;

int SW_COMBO_SITH_ATTACK = 14;

int SW_COMBO_BUFF_ATTACK = 15;

int SW_COMBO_SITH_CONFOUND = 16;

int SW_COMBO_JEDI_SMITE = 17;

int SW_COMBO_SITH_TAUNT = 18;

int SW_COMBO_SITH_BLADE = 19;

int SW_COMBO_SITH_CRUSH = 20;

int SW_COMBO_JEDI_CRUSH = 21;

int SW_COMBO_SITH_BRUTALIZE = 22;

int SW_COMBO_SITH_DRAIN = 23;

int SW_COMBO_SITH_ESCAPE = 24;

int SW_COMBO_JEDI_BLITZ = 25;

int SW_COMBO_SITH_SPIKE = 26;

int SW_COMBO_SITH_SCYTHE = 27;

int SW_COMBO_DROID_UTILITIES = 28;

int SW_COMBO_DROID_UTILITIES_2 = 29;

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 28, 2002

//:://////////////////////////////////////////////

int GN_GetStandardJediCombo(int nBoss = FALSE)

{

    int nBool;

    int nRand;

    while(nBool == FALSE)

    {

        if(nBoss == FALSE)

        {

            nRand = Random(23)+1;



            if(nRand == 1 || nRand == 2) {return SW_COMBO_MELEE_FEROCIOUS;}

            else if(nRand == 3 || nRand == 4) {return SW_COMBO_MELEE_AGGRESSIVE;}

            else if(nRand == 5 || nRand == 6) {return SW_COMBO_MELEE_DISCIPLINED;}

            else if(nRand == 7 || nRand == 8 || nRand == 9) {return SW_COMBO_MELEE_CAUTIOUS;}

            else if(nRand >= 10 || nRand <= 24)

            {

                nRand = nRand+3;

            }

        }

        else

        {

            nRand = Random(15);

            nRand = nRand + 13;

        }



        nBool = GN_GetIsComboValid(nRand);

        //GN_MyPrintString("GENERIC DEBUG *************** Jedi Combo " + GN_FetchComboString(nRand) + " is " + IntToString(nBool));

    }

    return nRand;

}

//::///////////////////////////////////////////////

//:: Get Droid Combo

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns a proper Droid Combo for Standard AI

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 28, 2002

//:://////////////////////////////////////////////

int GN_GetStandardDroidCombo(int nBoss = FALSE)

{

    //GN_MyPrintString("GENERIC DEBUG *************** Droid Combo Selection Started");

    int nBool = FALSE;

    int nRand = d6();

    while(nBool == FALSE)

    {

        if(nRand == 1){nRand = SW_COMBO_RANGED_AGGRESSIVE;}

        else if(nRand == 2){nRand = SW_COMBO_RANGED_CAUTIOUS;}

        else if(nRand == 3){nRand = SW_COMBO_RANGED_DISCIPLINED;}

        else if(nRand == 4){nRand = SW_COMBO_RANGED_FEROCIOUS;}

        else if(nRand == 5 || nRand == 6)

        {

            if((IsObjectPartyMember(OBJECT_SELF) && GetNPCAIStyle(OBJECT_SELF) == NPC_AISTYLE_JEDI_SUPPORT) ||

                !IsObjectPartyMember(OBJECT_SELF))

            {

                if(nRand == 5)

                {

                    nRand = SW_COMBO_DROID_UTILITIES;

                }

                else if(nRand == 6)

                {

                    nRand = SW_COMBO_DROID_UTILITIES_2;

                }

            }

            else

            {

                nRand = SW_COMBO_INVALID;

            }

        }



        nBool = GN_GetIsComboValid(nRand);

        //GN_MyPrintString("GENERIC DEBUG *************** Droid Combo Picked " + GN_FetchComboString(nRand) + " is " + IntToString(nBool));

        if(nBool == FALSE)

        {

            nRand = d6();

        }

    }

    //GN_MyPrintString("GENERIC DEBUG *************** Returning Combo Returned = " + GN_FetchComboString(nRand));

    return nRand;

}



//::///////////////////////////////////////////////

//:: Get NPC Combo

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns a proper NPC Combo for Standard AI

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 28, 2002

//:://////////////////////////////////////////////

int GN_GetStandardNPCCombo(int nBoss = FALSE)

{

    int nBool;

    int nRand = d4();

    if(GN_GetWeaponType() != 0)

    {

        while(nBool == FALSE)

        {

            if(GN_GetWeaponType() == 1)

            {

                if(nRand == 1){nRand = SW_COMBO_MELEE_AGGRESSIVE;}

                else if(nRand == 2){nRand = SW_COMBO_MELEE_CAUTIOUS;}

                else if(nRand == 3){nRand = SW_COMBO_MELEE_DISCIPLINED;}

                else if(nRand == 4){nRand = SW_COMBO_MELEE_FEROCIOUS;}

            }

            else if(GN_GetWeaponType() == 2)

            {

                if(nRand == 1){nRand = SW_COMBO_RANGED_AGGRESSIVE;}

                else if(nRand == 2){nRand = SW_COMBO_RANGED_CAUTIOUS;}

                else if(nRand == 3){nRand = SW_COMBO_RANGED_DISCIPLINED;}

                else if(nRand == 4){nRand = SW_COMBO_RANGED_FEROCIOUS;}

            }

            nBool = GN_GetIsComboValid(nRand);

            if(nBool == FALSE)

            {

                nRand = d6();

            }

        }

    }

    else

    {

        nRand = 2;

    }

    //GN_MyPrintString("GENERIC DEBUG *************** NPC Combo " + GN_FetchComboString(nRand) + " is " + IntToString(nBool));

    return nRand;

}



//::///////////////////////////////////////////////

//:: Get Next Talent In Combo

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Looks at the combo id and returns an ability

    usable by the NPC which matches the next

    feat in the combo.

*/



//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 27, 2002

//:://////////////////////////////////////////////

talent GN_GetNextTalentInCombo(int nCombo)

{

    SetLocalBoolean(OBJECT_SELF, SW_FLAG_TARGET_FRIEND, FALSE);

    int nLocal = GetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_INDEX);

    //GN_MyPrintString("GENERIC DEBUG *************** Combo Index " + IntToString(nLocal));

    talent tUse, tInvalid;

    int nID = -1;

    int nFeat = FALSE;

    int nBuff = FALSE;

    //Sith Attack(PUSH, CHOKE, JUMP)

    if(nCombo == SW_COMBO_SITH_ATTACK)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesChoke();

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesForcePush();

        }

        else

        {

            nID = GN_GetSeriesJump();

        }

    }

    //Buff Attack(ARMOR, SPEED, FEAT)

    else if(nCombo == SW_COMBO_BUFF_ATTACK)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesForceArmor();

            nBuff = TRUE;

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesSpeed();

            nBuff = TRUE;

        }

        else

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

    }

    //Sith Confound (FEAR, FEAT, FEAT)

    else if(nCombo == SW_COMBO_SITH_CONFOUND)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesLightning();

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

        else

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

    }

    //Jedi Smite (HOLD, FEAT, FEAT)

    else if(nCombo == SW_COMBO_JEDI_SMITE)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesHold();

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

        else

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

    }

    //Sith Taunt (CHOKE, POISON, FEAT)

    else if(nCombo == SW_COMBO_SITH_TAUNT)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesChoke();

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesAfflict();

        }

        else

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

    }

    //Sith Blade (SLOW, PUSH, THROW)

    else if(nCombo == SW_COMBO_SITH_BLADE)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesAfflict();

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesForcePush();

        }

        else

        {

            nID = GN_GetSeriesSaberThrow();

        }

    }

    //Sith Crush (PUSH, SHOCK, JUMP)

    else if(nCombo == SW_COMBO_SITH_CRUSH)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesLightning();

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesForcePush();

        }

        else

        {

            nID = GN_GetSeriesJump();

        }

    }

    //Jedi Crush (HOLD, THROW, JUMP)

    else if(nCombo == SW_COMBO_JEDI_CRUSH)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesHold();

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesForcePush();

        }

        else

        {

            nID = GN_GetSeriesJump();

        }

    }

    //Sith Brutalize (CHOKE, DRAIN, PUSH)

    else if(nCombo == SW_COMBO_SITH_BRUTALIZE)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesChoke();

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesDrainLife();

        }

        else

        {

            nID = GN_GetSeriesForcePush();

        }

    }

    //Sith Drain (FEAT, DRAIN, FEAT)

    else if(nCombo == SW_COMBO_SITH_DRAIN)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesDrainLife();

        }

        else

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

    }

    //Sith Escape (DRAIN, PUSH, THROW)

    else if(nCombo == SW_COMBO_SITH_ESCAPE)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesDrainLife();

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesForcePush();

        }

        else

        {

            nID = GN_GetSeriesSaberThrow();

        }

    }

    //Jedi Blitz (FEAT, FEAT, PUSH)

    else if(nCombo == SW_COMBO_JEDI_BLITZ)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

        else

        {

            nID = GN_GetSeriesForcePush();

        }

    }

    //Sith Spike (PUSH, SLOW, FEAT)

    else if(nCombo == SW_COMBO_SITH_SPIKE)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesAfflict();

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

        else

        {

            nID = GN_GetSeriesForcePush();

        }

    }

    //Sith Scythe (DRAIN, FEAR, FEAT)

    else if(nCombo == SW_COMBO_SITH_SCYTHE)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesDrainLife();

        }

        else if (nLocal == 2)

        {

            nID = GN_GetSeriesBreach();

        }

        else

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

    }

    //Melee Ferocious (USE 3 FEATS)

    else if(nCombo == SW_COMBO_MELEE_FEROCIOUS)

    {

        nID = GN_GetSeriesMeleeFeat();

        nFeat = TRUE;

    }

    //Melee Aggressive (USE 2 FEATS)

    else if(nCombo == SW_COMBO_MELEE_AGGRESSIVE)

    {

        if(nLocal == 1 || nLocal == 2)

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

        else

        {

            //GN_MyPrintString("GENERIC DEBUG *************** Melee/Ranged Breather");

        }

    }

    //Melee Discipline (USE 1 FEAT)

    else if(nCombo == SW_COMBO_MELEE_DISCIPLINED)

    {

        if(nLocal == 1 || nLocal == 2)

        {

            nID = GN_GetSeriesMeleeFeat();

            nFeat = TRUE;

        }

        else

        {

            //GN_MyPrintString("GENERIC DEBUG *************** Melee/Ranged Breather");

        }

    }

    else if(nCombo == SW_COMBO_MELEE_CAUTIOUS || nCombo == SW_COMBO_RANGED_CAUTIOUS)

    {

        GN_MyPrintString("GENERIC DEBUG *************** Melee/Ranged Breather");

    }

    //Melee Cautious (USE NO FEATS) //This does not require a check. It will return an invalid talent

    //Ranged Cautious (USE NO FEATS) //This does not require a check. It will return an invalid talent

    //Ranged Ferocious (USE 3 FEATS)

    else if(nCombo == SW_COMBO_RANGED_FEROCIOUS)

    {

        nID = GN_GetSeriesRangedFeat();

        nFeat = TRUE;

    }

    //Ranged Aggressive (USE 2 FEATS)

    else if(nCombo == SW_COMBO_RANGED_AGGRESSIVE)

    {

        if(nLocal == 1 || nLocal == 2)

        {

            nID = GN_GetSeriesRangedFeat();

            nFeat = TRUE;

        }

        else

        {

            //GN_MyPrintString("GENERIC DEBUG *************** Melee/Ranged Breather");

        }

    }

    //Ranged Discipline (USE 1 FEAT)

    else if(nCombo == SW_COMBO_RANGED_DISCIPLINED)

    {

        if(nLocal == 1 || nLocal == 2)

        {

            nID = GN_GetSeriesRangedFeat();

            nFeat = TRUE;

        }

        else

        {

            //GN_MyPrintString("GENERIC DEBUG *************** Melee/Ranged Breather");

        }

    }

    //Buff Party

    else if(nCombo == SW_COMBO_BUFF_PARTY)

    {

        tUse = GetCreatureTalentRandom(0xf8ff);

    }

    //Buff & Debilitate (BUFF & 2 DEBILITATE ENEMY)

    else if(nCombo == SW_COMBO_BUFF_DEBILITATE)

    {

        if(nLocal == 1)

        {

            tUse = GetCreatureTalentRandom(0xf8ff);

        }

        else

        {

            tUse = GetCreatureTalentRandom(0xf2ff);

        }

    }

    //Buff & Damage (BUFF  & 2 DAMAGE ENEMY)

    else if(nCombo == SW_COMBO_BUFF_DAMAGE)

    {

        if(nLocal == 1)

        {

            tUse = GetCreatureTalentRandom(0xf8ff);

        }

        else

        {

            tUse = GetCreatureTalentRandom(0xf1ff);

        }

    }

    //Buff, Debilitate & Destroy (1 BUFF, 1 DEBILITATE, 1 DESTROY)

    else if(nCombo == SW_COMBO_BUFF_DEBILITATE_DESTROY)

    {

        if(nLocal == 1)

        {

            tUse = GetCreatureTalentRandom(0xf8ff);

        }

        if(nLocal == 2)

        {

            tUse = GetCreatureTalentRandom(0xf2ff);

        }

        if(nLocal == 3)

        {

            tUse = GetCreatureTalentRandom(0x1101);

        }

    }

    //Supress, Debilitate & Destroy (1 Supress, 1 DEBILITATE, 1 DESTROY)

    else if(nCombo == SW_COMBO_SUPRESS_DEBILITATE_DESTROY)

    {

        if(nLocal == 1)

        {

            tUse = GetCreatureTalentRandom(0xf1ff);

        }

        if(nLocal == 2)

        {

            tUse = GetCreatureTalentRandom(0xf2ff);

        }

        if(nLocal == 3)

        {

            tUse = GetCreatureTalentRandom(0x1101);

        }

    }

    else if(nCombo == SW_COMBO_DROID_UTILITIES)

    {

        if(nLocal == 1)

        {

            nID = GN_GetSeriesRangedFeat();

            nFeat = TRUE;

        }

        if(nLocal == 2)

        {

            nID = GN_GetSeriesRangedFeat();

            nFeat = TRUE;

        }

        if(nLocal == 3)

        {

            tUse = GetCreatureTalentRandom(0x8000);

        }

    }

    else if(nCombo == SW_COMBO_DROID_UTILITIES_2)

    {

        if(nLocal == 1)

        {

            tUse = GetCreatureTalentRandom(0x8000);

        }

        if(nLocal == 2)

        {

            nID = GN_GetSeriesRangedFeat();

            nFeat = TRUE;

        }

        if(nLocal == 3)

        {

            tUse = GetCreatureTalentRandom(0x8000);

        }

    }



    //Increments the Local number so that the progression through the Combo continues even if the talent fails

    nLocal++;

    SetLocalNumber(OBJECT_SELF, SW_NUMBER_COMBO_INDEX, nLocal);

    if(!GetIsTalentValid(tUse) || !GetCreatureHasTalent(tUse))

    {

        //GN_MyPrintString("GENERIC DEBUG *************** ID = " + IntToString(nID));

        if(nID != -1 && nFeat == FALSE)

        {

            //GN_MyPrintString("GENERIC DEBUG *************** Spell ID = " + IntToString(nID));

            tUse = TalentSpell(nID);

        }

        else if(nID != -1 && nFeat == TRUE)

        {

            //GN_MyPrintString("GENERIC DEBUG *************** Feat ID = " + IntToString(nID));

            tUse = TalentFeat(nID);

        }

    }

    else

    {

        nID = GetIdFromTalent(tUse);

        //GN_MyPrintString("GENERIC DEBUG *************** Preselected ID = " + IntToString(nID));

    }

    //Use GetCreatureHasTalent here to make the talent is currently usable - ie enough force points.

    //Currently it terminates the script, so do not use it.

    if(GetIsTalentValid(tUse) && GetCreatureHasTalent(tUse))

    {

        //GN_MyPrintString("GENERIC DEBUG *************** Returning Valid Talent");

        return tUse;

    }

    //GN_MyPrintString("GENERIC DEBUG *************** Returning Invalid Talent");

    return tInvalid;

}



//::///////////////////////////////////////////////

//:: Force Power Get Functions

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns an ability based.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 27, 2002

//:://////////////////////////////////////////////

int GN_GetSeriesForcePush()

{

    if(GetHasSpell(FORCE_POWER_FORCE_WAVE))

    {

        return FORCE_POWER_FORCE_WAVE;

    }

    else if(GetHasSpell(FORCE_POWER_FORCE_WHIRLWIND))

    {

        return FORCE_POWER_FORCE_WHIRLWIND;

    }

    else if(GetHasSpell(FORCE_POWER_FORCE_PUSH))

    {

        return FORCE_POWER_FORCE_PUSH;

    }

    return -1;

}

int GN_GetSeriesForceArmor()

{

    if(GetHasSpell(FORCE_POWER_FORCE_ARMOR))

    {

        return FORCE_POWER_FORCE_ARMOR;

    }

    else if(GetHasSpell(FORCE_POWER_FORCE_SHIELD))

    {

        return FORCE_POWER_FORCE_SHIELD;

    }

    else if(GetHasSpell(FORCE_POWER_FORCE_AURA))

    {

        return FORCE_POWER_FORCE_AURA;

    }

    return -1;

}

int GN_GetSeriesFear()

{

    if(GetHasSpell(FORCE_POWER_INSANITY))

    {

        return FORCE_POWER_INSANITY;

    }

    else if(GetHasSpell(FORCE_POWER_HORROR))

    {

        return FORCE_POWER_HORROR;

    }

    else if(GetHasSpell(FORCE_POWER_FEAR))

    {

        return FORCE_POWER_FEAR;

    }

    return -1;

}

int GN_GetSeriesHold()

{

    if(GetHasSpell(FORCE_POWER_SLEEP))

    {

        return FORCE_POWER_SLEEP;

    }

    else if(GetHasSpell(FORCE_POWER_HOLD))

    {

        return FORCE_POWER_HOLD;

    }

    else if(GetHasSpell(FORCE_POWER_STUN))

    {

        return FORCE_POWER_STUN;

    }

    return -1;

}

int GN_GetSeriesAfflict()

{

    if(GetHasSpell(FORCE_POWER_PLAGUE))

    {

        return FORCE_POWER_PLAGUE;

    }

    else if(GetHasSpell(FORCE_POWER_AFFLICTION))

    {

        return FORCE_POWER_AFFLICTION;

    }

    else if(GetHasSpell(FORCE_POWER_SLOW))

    {

        return FORCE_POWER_SLOW;

    }

    return -1;

}

int GN_GetSeriesSaberThrow()

{

    if(GetHasSpell(FORCE_POWER_LIGHT_SABER_THROW_ADVANCED))

    {

        return FORCE_POWER_LIGHT_SABER_THROW_ADVANCED;

    }

    else if(GetHasSpell(FORCE_POWER_LIGHT_SABER_THROW))

    {

        return FORCE_POWER_LIGHT_SABER_THROW;

    }

    return -1;

}

int GN_GetSeriesLightning()

{

    if(GetHasSpell(FORCE_POWER_FORCE_STORM))

    {

        return FORCE_POWER_FORCE_STORM;

    }

    else if(GetHasSpell(FORCE_POWER_LIGHTNING))

    {

        return FORCE_POWER_LIGHTNING;

    }

    else if(GetHasSpell(FORCE_POWER_SHOCK))

    {

        return FORCE_POWER_SHOCK;

    }

    return -1;

}

int GN_GetSeriesJump()

{

    if(GetHasSpell(FORCE_POWER_FORCE_JUMP_ADVANCED))

    {

        return FORCE_POWER_FORCE_JUMP_ADVANCED;

    }

    else if(GetHasSpell(FORCE_POWER_FORCE_JUMP))

    {

        return FORCE_POWER_FORCE_JUMP;

    }

    return -1;

}

int GN_GetSeriesChoke()

{

    if(GetHasSpell(FORCE_POWER_KILL))

    {

        return FORCE_POWER_KILL;

    }

    else if(GetHasSpell(FORCE_POWER_CHOKE))

    {

        return FORCE_POWER_CHOKE;

    }

    else if(GetHasSpell(FORCE_POWER_WOUND))

    {

        return FORCE_POWER_WOUND;

    }

    return -1;

}

int GN_GetSeriesDrainLife()

{

    if(GetHasSpell(FORCE_POWER_DEATH_FIELD))

    {

        return FORCE_POWER_DEATH_FIELD;

    }

    else if(GetHasSpell(FORCE_POWER_DRAIN_LIFE))

    {

        return FORCE_POWER_DRAIN_LIFE;

    }

    return -1;

}

int GN_GetSeriesSpeed()

{

    if(GetHasSpell(FORCE_POWER_SPEED_MASTERY))

    {

        return FORCE_POWER_SPEED_MASTERY;

    }

    else if(GetHasSpell(FORCE_POWER_KNIGHT_SPEED))

    {

        return FORCE_POWER_KNIGHT_SPEED;

    }

    else if(GetHasSpell(FORCE_POWER_SPEED_BURST))

    {

        return FORCE_POWER_SPEED_BURST;

    }

    return -1;

}

int GN_GetSeriesMeleeFeat()

{

    talent tUse = GetCreatureTalentBest(0x1104, 20);

    if(GetIsTalentValid(tUse) && GetCreatureHasTalent(tUse))

    {

        int nID = GetIdFromTalent(tUse);

        return nID;

    }

    return -1;

}

int GN_GetSeriesRangedFeat()

{

    talent tUse = GetCreatureTalentBest(0x1181, 20);

    if(GetIsTalentValid(tUse) && GetCreatureHasTalent(tUse))

    {

        int nID = GetIdFromTalent(tUse);

        return nID;

    }

    return -1;

}

int GN_GetSeriesMind()

{

    if(GetHasSpell(FORCE_POWER_MIND_MASTERY))

    {

        return FORCE_POWER_MIND_MASTERY;

    }

    else if(GetHasSpell(FORCE_POWER_KNIGHT_MIND))

    {

        return FORCE_POWER_KNIGHT_MIND;

    }

    else if(GetHasSpell(FORCE_POWER_FORCE_MIND))

    {

        return FORCE_POWER_FORCE_MIND;

    }

    return -1;

}

int GN_GetSeriesResist()

{

    if(GetHasSpell(FORCE_POWER_RESIST_COLD_HEAT_ENERGY))

    {

        return FORCE_POWER_RESIST_COLD_HEAT_ENERGY;

    }

    else if(GetHasSpell(FORCE_POWER_RESIST_POISON_DISEASE_SONIC))

    {

        return FORCE_POWER_RESIST_POISON_DISEASE_SONIC;

    }

    return -1;

}

int GN_GetSeriesForceImmunity()

{

    if(GetHasSpell(FORCE_POWER_FORCE_IMMUNITY))

    {

        return FORCE_POWER_FORCE_IMMUNITY;

    }

    else if(GetHasSpell(FORCE_POWER_RESIST_FORCE))

    {

        return FORCE_POWER_RESIST_FORCE;

    }

    return -1;

}

int GN_GetSeriesBreach()

{

    if(GetHasSpell(FORCE_POWER_FORCE_BREACH))

    {

        return FORCE_POWER_FORCE_BREACH;

    }

    else if(GetHasSpell(FORCE_POWER_SUPRESS_FORCE))

    {

        return FORCE_POWER_SUPRESS_FORCE;

    }

    return -1;

}



//::///////////////////////////////////////////////

//:: Force Power Series Checks

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks if a Jedi has 1 in a force power series

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 27, 2002

//:://////////////////////////////////////////////



int GN_CheckSeriesForcePush()

{

    if(GetHasSpell(FORCE_POWER_FORCE_PUSH) || GetHasSpell(FORCE_POWER_FORCE_WHIRLWIND) || GetHasSpell(FORCE_POWER_FORCE_WAVE))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesArmor()

{

    if(GetHasSpell(FORCE_POWER_FORCE_ARMOR) || GetHasSpell(FORCE_POWER_FORCE_SHIELD) || GetHasSpell(FORCE_POWER_FORCE_AURA))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesFear()

{

    if(GetHasSpell(FORCE_POWER_FEAR) || GetHasSpell(FORCE_POWER_HORROR) || GetHasSpell(FORCE_POWER_INSANITY))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesHold()

{

    if(GetHasSpell(FORCE_POWER_STUN) || GetHasSpell(FORCE_POWER_HOLD) || GetHasSpell(FORCE_POWER_SLEEP))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesAfflict()

{

    if(GetHasSpell(FORCE_POWER_SLOW) || GetHasSpell(FORCE_POWER_AFFLICTION) || GetHasSpell(FORCE_POWER_PLAGUE))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesSaberThrow()

{

    if(GetHasSpell(FORCE_POWER_LIGHT_SABER_THROW) || GetHasSpell(FORCE_POWER_LIGHT_SABER_THROW_ADVANCED))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesLightning()

{

    if(GetHasSpell(FORCE_POWER_SHOCK) || GetHasSpell(FORCE_POWER_LIGHTNING) || GetHasSpell(FORCE_POWER_FORCE_STORM))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesJump()

{

    if(GetHasSpell(FORCE_POWER_FORCE_JUMP) || GetHasSpell(FORCE_POWER_FORCE_JUMP_ADVANCED))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesChoke()

{

    if(GetHasSpell(FORCE_POWER_CHOKE) || GetHasSpell(FORCE_POWER_WOUND) || GetHasSpell(FORCE_POWER_KILL))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesDrainLife()

{

    if(GetHasSpell(FORCE_POWER_DRAIN_LIFE) || GetHasSpell(FORCE_POWER_DEATH_FIELD))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesSpeed()

{

    if(GetHasSpell(FORCE_POWER_SPEED_BURST) || GetHasSpell(FORCE_POWER_SPEED_MASTERY) || GetHasSpell(FORCE_POWER_KNIGHT_SPEED))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesMind()

{

    if(GetHasSpell(FORCE_POWER_MIND_MASTERY) || GetHasSpell(FORCE_POWER_KNIGHT_MIND) || GetHasSpell(FORCE_POWER_FORCE_MIND))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesResist()

{

    if(GetHasSpell(FORCE_POWER_RESIST_COLD_HEAT_ENERGY) || GetHasSpell(FORCE_POWER_RESIST_POISON_DISEASE_SONIC))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesForceImmunity()

{

    if(GetHasSpell(FORCE_POWER_RESIST_FORCE) || GetHasSpell(FORCE_POWER_FORCE_IMMUNITY))

    {

        return TRUE;

    }

    return FALSE;

}

int GN_CheckSeriesBreach()

{

    if(GetHasSpell(FORCE_POWER_SUPRESS_FORCE) || GetHasSpell(FORCE_POWER_FORCE_BREACH))

    {

        return TRUE;

    }

    return FALSE;

}



int GN_CheckSeriesDroidUtilities()

{

    talent tUse = GetCreatureTalentRandom(0x8000);

    /*

    if(GetHasSpell(116) || GetHasSpell(117) || GetHasSpell(118) ||

       GetHasSpell(119) || GetHasSpell(120) || GetHasSpell(121) ||

       GetHasSpell(121) || GetHasSpell(122) || GetHasSpell(123) ||

       GetHasSpell(124) || GetHasSpell(125))

    */

    if(GetIsTalentValid(tUse))

    {

        return TRUE;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Is Combo Valid

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Gets a combo constant and determines if the

    NPC can perform the stated combo

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 27, 2002

//:://////////////////////////////////////////////



int GN_GetIsComboValid(int nComboType)

{

    //P.W (May 27, 2003) - Made allowances for an invalid effect to be passed in.

    if(nComboType == SW_COMBO_INVALID)

    {

        return FALSE;

    }



    talent tTest, tTest2;

    if(nComboType == SW_COMBO_MELEE_FEROCIOUS ||

            nComboType == SW_COMBO_MELEE_AGGRESSIVE ||

            nComboType == SW_COMBO_MELEE_DISCIPLINED)

    {

        tTest = GetCreatureTalentRandom(0x1104); //Only Melee feats use this code

        if(GetIsTalentValid(tTest) && GetCreatureHasTalent(tTest))

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_RANGED_CAUTIOUS)

    {

        return TRUE;

    }

    else if(nComboType == SW_COMBO_RANGED_FEROCIOUS ||

       nComboType == SW_COMBO_RANGED_AGGRESSIVE ||

       nComboType == SW_COMBO_RANGED_DISCIPLINED)

    {

        //These are the only ranged feats in the game and therefore it is better to use a feat constant not a talent code

        //given that 0x1101 is also used by some force powers.

        if(GetHasFeat(FEAT_SNIPER_SHOT) || GetHasFeat(FEAT_IMPROVED_SNIPER_SHOT) || GetHasFeat(FEAT_MASTER_SNIPER_SHOT) ||

           GetHasFeat(FEAT_POWER_BLAST) || GetHasFeat(FEAT_IMPROVED_POWER_BLAST) || GetHasFeat(82) || //Master Power Blast

           GetHasFeat(FEAT_RAPID_SHOT) || GetHasFeat(FEAT_MULTI_SHOT) || GetHasFeat(92))//92 = IMRPOVED_RAPID_SHOT

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_MELEE_CAUTIOUS)

    {

        return TRUE;

    }

    else if(nComboType == SW_COMBO_BUFF_PARTY)

    {

        tTest = GetCreatureTalentRandom(0xf8ff);

        if(GetIsTalentValid(tTest) && GetCreatureHasTalent(tTest))

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_BUFF_DEBILITATE)

    {

        tTest = GetCreatureTalentRandom(0xf8ff);

        tTest2 = GetCreatureTalentRandom(0xf2ff);

        if(GetIsTalentValid(tTest) && GetIsTalentValid(tTest2)

           && GetCreatureHasTalent(tTest)

           && GetCreatureHasTalent(tTest2))

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_BUFF_DAMAGE)

    {

        tTest = GetCreatureTalentRandom(0xf8ff);

        if(GetIsTalentValid(tTest) && GN_GetHasDamagingForcePower())

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_BUFF_DEBILITATE_DESTROY)

    {

        tTest = GetCreatureTalentRandom(0xf8ff);

        tTest2 = GetCreatureTalentRandom(0xf2ff);

        if(GetIsTalentValid(tTest) && GetIsTalentValid(tTest2) && GN_GetHasDamagingForcePower())

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_SUPRESS_DEBILITATE_DESTROY)

    {

        tTest = GetCreatureTalentRandom(0xff2f);

        tTest2 = GetCreatureTalentRandom(0xf2ff);

        if(GetIsTalentValid(tTest) && GetIsTalentValid(tTest2) && GN_GetHasDamagingForcePower())

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_SITH_ATTACK)

    {

        if(GN_CheckSeriesForcePush() && GN_CheckSeriesChoke() && GN_CheckSeriesJump())

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_BUFF_ATTACK)

    {

        tTest = GetCreatureTalentRandom(0x1104);

        if(GN_CheckSeriesArmor() && GN_CheckSeriesSpeed() && GetIsTalentValid(tTest))

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_SITH_CONFOUND)

    {

        tTest = GetCreatureTalentRandom(0x1104);

        if(GN_CheckSeriesLightning() && GetIsTalentValid(tTest))

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_JEDI_SMITE)

    {

        tTest = GetCreatureTalentRandom(0x1104);

        if(GN_CheckSeriesHold() && GetIsTalentValid(tTest))

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_SITH_TAUNT)

    {

        tTest = GetCreatureTalentRandom(0x1104);

        if(GN_CheckSeriesChoke() && GN_CheckSeriesAfflict() && GetIsTalentValid(tTest))

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_SITH_BLADE)

    {

        if(GN_CheckSeriesAfflict() && GN_CheckSeriesForcePush() && GN_CheckSeriesSaberThrow())

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_SITH_CRUSH)

    {

        if(GN_CheckSeriesLightning() && GN_CheckSeriesForcePush() && GN_CheckSeriesJump())

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_JEDI_CRUSH)

    {

        if(GN_CheckSeriesHold() && GN_CheckSeriesForcePush() && GN_CheckSeriesJump())

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_JEDI_CRUSH)

    {

        if(GN_CheckSeriesChoke() && GN_CheckSeriesDrainLife() && GN_CheckSeriesForcePush())

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_SITH_DRAIN)

    {

        tTest = GetCreatureTalentRandom(0x1104);

        if(GN_CheckSeriesDrainLife() && GetIsTalentValid(tTest))

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_SITH_ESCAPE)

    {

        if(GN_CheckSeriesDrainLife() && GN_CheckSeriesForcePush() && GN_CheckSeriesSaberThrow())

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_JEDI_BLITZ)

    {

        tTest = GetCreatureTalentRandom(0x1104);

        if(GN_CheckSeriesForcePush() && GetIsTalentValid(tTest))

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_SITH_SPIKE)

    {

        tTest = GetCreatureTalentRandom(0x1104);

        if(GN_CheckSeriesForcePush() && GN_CheckSeriesAfflict() && GetIsTalentValid(tTest))

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_SITH_SCYTHE)

    {

        tTest = GetCreatureTalentRandom(0x1104);

        if(GN_CheckSeriesDrainLife() && GN_CheckSeriesBreach() && GetIsTalentValid(tTest))

        {

            return TRUE;

        }

    }

    else if(nComboType == SW_COMBO_DROID_UTILITIES || nComboType == SW_COMBO_DROID_UTILITIES_2)

    {

        object oItem1 = GetItemInSlot(INVENTORY_SLOT_LEFTARM);

        object oItem2 = GetItemInSlot(INVENTORY_SLOT_RIGHTARM);



        GN_MyPrintString("GENERIC DEBUG *************** Droid Items = " + GN_ReturnDebugName(oItem1) + " / " + GN_ReturnDebugName(oItem2));



        if(GN_CheckSeriesDroidUtilities())

        {

            GN_MyPrintString("GENERIC DEBUG *************** Droid Utility Check is TRUE");

            return TRUE;

        }

        GN_MyPrintString("GENERIC DEBUG *************** Droid Utility Check is FALSE");

    }

    return FALSE;

}



int GN_GetHasDamagingForcePower()

{

    if(GetHasSpell(FORCE_POWER_CHOKE) ||

       GetHasSpell(FORCE_POWER_DEATH_FIELD) ||

       GetHasSpell(FORCE_POWER_DRAIN_LIFE) ||

       GetHasSpell(FORCE_POWER_DROID_DESTROY) ||

       GetHasSpell(FORCE_POWER_DROID_DISABLE) ||

       GetHasSpell(FORCE_POWER_FORCE_PUSH) ||

       GetHasSpell(FORCE_POWER_FORCE_STORM) ||

       GetHasSpell(FORCE_POWER_FORCE_WAVE) ||

       GetHasSpell(FORCE_POWER_FORCE_WHIRLWIND) ||

       GetHasSpell(FORCE_POWER_KILL) ||

       GetHasSpell(FORCE_POWER_LIGHT_SABER_THROW) ||

       GetHasSpell(FORCE_POWER_LIGHT_SABER_THROW_ADVANCED) ||

       GetHasSpell(FORCE_POWER_LIGHTNING) ||

       GetHasSpell(FORCE_POWER_SHOCK) ||

       GetHasSpell(FORCE_POWER_WOUND))

    {

        return TRUE;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Get Weapon Type

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Return 1 if the object is a Melee Weapon and

    2 if the weapon is a Ranged Weapon

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 2, 2002

//:://////////////////////////////////////////////



int GN_GetWeaponType(object oTarget = OBJECT_SELF)

{

    object oItem = GetItemInSlot(INVENTORY_SLOT_RIGHTWEAPON,oTarget);

    //GN_MyPrintString("GENERIC DEBUG *************** Valid Weapon = " + GN_ITS(GetIsObjectValid(oItem)));

    if(GetIsObjectValid(oItem))

    {

        if( GetBaseItemType(oItem) == BASE_ITEM_BLASTER_CARBINE ||

           GetBaseItemType(oItem) == BASE_ITEM_BLASTER_PISTOL ||

           GetBaseItemType(oItem) == BASE_ITEM_BLASTER_RIFLE ||

           GetBaseItemType(oItem) == BASE_ITEM_BOWCASTER ||

           GetBaseItemType(oItem) == BASE_ITEM_DISRUPTER_PISTOL ||

           GetBaseItemType(oItem) == BASE_ITEM_DISRUPTER_RIFLE ||

           GetBaseItemType(oItem) == BASE_ITEM_HEAVY_BLASTER ||

           GetBaseItemType(oItem) == BASE_ITEM_HEAVY_REPEATING_BLASTER ||

           GetBaseItemType(oItem) == BASE_ITEM_HOLD_OUT_BLASTER ||

           GetBaseItemType(oItem) == BASE_ITEM_ION_BLASTER ||

           GetBaseItemType(oItem) == BASE_ITEM_ION_RIFLE ||

           GetBaseItemType(oItem) == BASE_ITEM_REPEATING_BLASTER ||

           GetBaseItemType(oItem) == BASE_ITEM_SONIC_PISTOL ||

           GetBaseItemType(oItem) == BASE_ITEM_SONIC_RIFLE ||

           GetBaseItemType(oItem) == BASE_ITEM_SONIC_PISTOL )

        {

            //GN_MyPrintString("GENERIC DEBUG *************** Ranged Weapon Equipped");

            return 2;

        }

        else if( GetBaseItemType(oItem) == BASE_ITEM_DOUBLE_BLADED_LIGHTSABER ||

           GetBaseItemType(oItem) == BASE_ITEM_DOUBLE_BLADED_SWORD ||

           GetBaseItemType(oItem) == BASE_ITEM_GAMMOREAN_BATTLEAXE ||

           GetBaseItemType(oItem) == BASE_ITEM_GHAFFI_STICK ||

           GetBaseItemType(oItem) == BASE_ITEM_LIGHTSABER ||

           GetBaseItemType(oItem) == BASE_ITEM_LONG_SWORD ||

           GetBaseItemType(oItem) == BASE_ITEM_QUARTER_STAFF ||

           GetBaseItemType(oItem) == BASE_ITEM_SHORT_LIGHTSABER ||

           GetBaseItemType(oItem) == BASE_ITEM_SHORT_SWORD ||

           GetBaseItemType(oItem) == BASE_ITEM_STUN_BATON ||

           GetBaseItemType(oItem) == BASE_ITEM_VIBRO_BLADE ||

           GetBaseItemType(oItem) == BASE_ITEM_VIBRO_DOUBLE_BLADE ||

           GetBaseItemType(oItem) == BASE_ITEM_VIBRO_SWORD ||

           GetBaseItemType(oItem) == BASE_ITEM_WOOKIE_WARBLADE )

        {

            //GN_MyPrintString("GENERIC DEBUG *************** Melee Weapon Equipped");

            return 1;

        }

    }

    GN_MyPrintString("GENERIC DEBUG *************** Return No Weapon Type");

    return 0;

}



//

//::///////////////////////////////////////////////

//:: Equip Appropriate Weapon

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Gets the NPC to eqyuip a melee = 1 or

    ranged = 2 weapon.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 13, 2003

//:://////////////////////////////////////////////



int GN_EquipAppropriateWeapon()

{

    object oItem;

    if(GetIsObjectValid(GetAttackTarget()) &&

       GetDistanceBetween(GetAttackTarget(), OBJECT_SELF) <= 3.0 &&

       GN_GetWeaponType() != 1 &&

       GetRacialType(OBJECT_SELF) == RACIAL_TYPE_HUMAN &&

       !IsObjectPartyMember(OBJECT_SELF))

    {

        oItem = GetFirstItemInInventory();

        while(GetIsObjectValid(oItem))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Checking Melee Weapon");

            if( GetBaseItemType(oItem) == BASE_ITEM_DOUBLE_BLADED_LIGHTSABER ||

               GetBaseItemType(oItem) == BASE_ITEM_DOUBLE_BLADED_SWORD ||

               GetBaseItemType(oItem) == BASE_ITEM_GAMMOREAN_BATTLEAXE ||

               GetBaseItemType(oItem) == BASE_ITEM_GHAFFI_STICK ||

               GetBaseItemType(oItem) == BASE_ITEM_LIGHTSABER ||

               GetBaseItemType(oItem) == BASE_ITEM_LONG_SWORD ||

               GetBaseItemType(oItem) == BASE_ITEM_QUARTER_STAFF ||

               GetBaseItemType(oItem) == BASE_ITEM_SHORT_LIGHTSABER ||

               GetBaseItemType(oItem) == BASE_ITEM_SHORT_SWORD ||

               GetBaseItemType(oItem) == BASE_ITEM_STUN_BATON ||

               GetBaseItemType(oItem) == BASE_ITEM_VIBRO_BLADE ||

               GetBaseItemType(oItem) == BASE_ITEM_VIBRO_DOUBLE_BLADE ||

               GetBaseItemType(oItem) == BASE_ITEM_VIBRO_SWORD ||

               GetBaseItemType(oItem) == BASE_ITEM_WOOKIE_WARBLADE )

            {

                GN_MyPrintString("GENERIC DEBUG *************** Equipping Melee Weapon");

                //ActionEquipItem(oItem, INVENTORY_SLOT_RIGHTWEAPON, TRUE);

                ActionEquipMostDamagingMelee();

                return TRUE;

            }

            else

            {

              oItem = GetNextItemInInventory();

            }

        }

    }

    else if(GN_GetWeaponType() != 2 &&

            GetLevelByClass(CLASS_TYPE_JEDICONSULAR) == 0 &&

            GetLevelByClass(CLASS_TYPE_JEDIGUARDIAN) == 0 &&

            GetLevelByClass(CLASS_TYPE_JEDISENTINEL) == 0 &&

            //GetIsObjectValid(GetAttackTarget()) &&

            GetDistanceBetween(GetAttemptedAttackTarget(), OBJECT_SELF) > 3.0 &&

            !IsObjectPartyMember(OBJECT_SELF))

    {

        oItem = GetFirstItemInInventory();

        while(GetIsObjectValid(oItem))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Checking Ranged Weapon");

            if( GetBaseItemType(oItem) == BASE_ITEM_BLASTER_CARBINE ||

               GetBaseItemType(oItem) == BASE_ITEM_BLASTER_PISTOL ||

               GetBaseItemType(oItem) == BASE_ITEM_BLASTER_RIFLE ||

               GetBaseItemType(oItem) == BASE_ITEM_BOWCASTER ||

               GetBaseItemType(oItem) == BASE_ITEM_DISRUPTER_PISTOL ||

               GetBaseItemType(oItem) == BASE_ITEM_DISRUPTER_RIFLE ||

               GetBaseItemType(oItem) == BASE_ITEM_HEAVY_BLASTER ||

               GetBaseItemType(oItem) == BASE_ITEM_HEAVY_REPEATING_BLASTER ||

               GetBaseItemType(oItem) == BASE_ITEM_HOLD_OUT_BLASTER ||

               GetBaseItemType(oItem) == BASE_ITEM_ION_BLASTER ||

               GetBaseItemType(oItem) == BASE_ITEM_ION_RIFLE ||

               GetBaseItemType(oItem) == BASE_ITEM_REPEATING_BLASTER ||

               GetBaseItemType(oItem) == BASE_ITEM_SONIC_PISTOL ||

               GetBaseItemType(oItem) == BASE_ITEM_SONIC_RIFLE ||

               GetBaseItemType(oItem) == BASE_ITEM_SONIC_PISTOL )

              {

                GN_MyPrintString("GENERIC DEBUG *************** Equipping Ranged Weapon");

                //ActionEquipItem(oItem, INVENTORY_SLOT_RIGHTWEAPON, TRUE);

                ActionEquipMostDamagingRanged();

                return TRUE;

              }

              else

              {

                oItem = GetNextItemInInventory();

              }

         }

    }

    GN_MyPrintString("GENERIC DEBUG *************** Should not currently change weapons");

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Check Friendly Fire on Target

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Takes a target object and a radius and

    returns how many friendly targets

    are in that zone.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 17, 2003

//:://////////////////////////////////////////////



int GN_CheckFriendlyFireOnTarget(object oTarget, float fDistance = 4.0)

{

    int nCnt, nHD, nMyHD;

    nMyHD = GetHitDice(OBJECT_SELF);

    object oCheck = GetFirstObjectInShape(SHAPE_SPHERE, fDistance, GetLocation(oTarget));

    while(GetIsObjectValid(oCheck))

    {

        //P.W.(May 20, 2003) - Put a dead check here for whether the person being checked is dead.

        if(GetIsFriend(oCheck) && !GetIsDead(oCheck))

        {

            nCnt++;

        }

        oCheck = GetNextObjectInShape(SHAPE_SPHERE, fDistance, GetLocation(oTarget));

    }

    return nCnt;

}



//::///////////////////////////////////////////////

//:: Check For Enemies Around Target

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Takes a target object and a radius and

    returns how many targets of the enemy faction

    are in that zone.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 16, 2001

//:://////////////////////////////////////////////

int GN_CheckEnemyGroupingOnTarget(object oTarget, float fDistance = 4.0)

{

    int nCnt;

    object oCheck = GetFirstObjectInShape(SHAPE_SPHERE, fDistance, GetLocation(oTarget));

    while(GetIsObjectValid(oCheck))

    {

        //P.W.(May 20, 2003) - Put a dead check here for whether the person being checked is dead.

        if(GetIsEnemy(oCheck) && !GetIsDead(oCheck))

        {

            nCnt++;

        }

        oCheck = GetNextObjectInShape(SHAPE_SPHERE, fDistance, GetLocation(oTarget));

    }

    return nCnt;

}



//::///////////////////////////////////////////////

//:: Find Grenade Target

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Searches the area and marks a group as a viable

    target for a grenade

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 17m 2003

//:://////////////////////////////////////////////



object GN_FindGrenadeTarget()

{

    int nMinimum = 0;

    if(IsObjectPartyMember(OBJECT_SELF))

    {

        nMinimum = 1;

    }

    int nFriend = 0;

    int nEnemy = 0;

    int nEnemyCnt = 0;

    object oFinal;

    object oCheck = GetFirstObjectInShape(SHAPE_SPHERE, 40.0, GetLocation(OBJECT_SELF));

    while(GetIsObjectValid(oCheck))

    {

        if(GetObjectSeen(oCheck) && !GetIsDead(oCheck))

        {

            nFriend = GN_CheckFriendlyFireOnTarget(oCheck);

            nEnemy = GN_CheckEnemyGroupingOnTarget(oCheck);

            //GN_MyPrintString("GENERIC DEBUG *************** Friends " + GN_ITS(nFriend) + "Enemies" + GN_ITS(nEnemy));

            if(nEnemy > nMinimum && nFriend == 0 && nEnemyCnt < nEnemy)

            {

                oFinal = oCheck;

                nEnemyCnt = nEnemy;

            }

        }

        oCheck = GetNextObjectInShape(SHAPE_SPHERE, 40.0, GetLocation(OBJECT_SELF));

    }

    return oFinal;

}



//::///////////////////////////////////////////////

//:: Find Grenade Target

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Searches the area and marks a group as a

    viable target for a AOE force power

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 17m 2003

//:://////////////////////////////////////////////



object GN_FindAOETarget()

{

    int nEnemy = 0;

    int nEnemyCnt = 0;

    object oFinal;

    object oCheck = GetFirstObjectInShape(SHAPE_SPHERE, 30.0, GetLocation(OBJECT_SELF));

    while(GetIsObjectValid(oCheck))

    {

        nEnemy = GN_CheckEnemyGroupingOnTarget(oCheck,4.0);

        if(nEnemy > 2 && nEnemyCnt < nEnemy)

        {

            oFinal = oCheck;

            nEnemyCnt = nEnemy;

        }

        oCheck = GetNextObjectInShape(SHAPE_SPHERE, 30.0, GetLocation(OBJECT_SELF));

    }

    return oFinal;

}



//::///////////////////////////////////////////////

//:: Get Grenade Talent

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns a talent based on the target.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 17, 2003

//:://////////////////////////////////////////////



talent GN_GetGrenadeTalent(int nDroid = FALSE)

{

    talent tUse;

    int n87, n88, n89, n90, n91, n92, n93, n94, n95;

    int nRand = 0;



    int bValid = FALSE;

    int nCnt = 87;

    for(nCnt; nCnt < 96; nCnt++)

    {

        tUse = TalentSpell(nCnt);

        if(GetCreatureHasTalent(tUse))

        {

            switch(nCnt)

            {

                case 87:

                {

                    n87 = TRUE;

                    nRand++;

                }

                break;

                case 88:

                {

                    if(nDroid == FALSE)

                    {

                        n88 = TRUE;

                        nRand++;

                    }

                }

                break;

                case 89:

                {

                    n89 = TRUE;

                    nRand++;

                }

                break;

                case 90:

                {

                    if(nDroid == FALSE)

                    {

                        n90 = TRUE;

                        nRand++;

                    }

                }

                break;

                case 91:

                {

                    if(nDroid == FALSE)

                    {

                        n91 = TRUE;

                        nRand++;

                    }

                }

                break;

                case 92:

                {

                    if(nDroid == FALSE)

                    {

                        n92 = TRUE;

                        nRand++;

                    }

                }

                break;

                case 93:

                {

                    if(nDroid == FALSE)

                    {

                        n93 = TRUE;

                        nRand++;

                    }

                }

                break;

                case 94:

                {

                    n94 = TRUE;

                    nRand++;

                }

                break;

                case 95:

                {

                    if(nDroid == TRUE)

                    {

                        n95 = TRUE;

                        nRand++;

                    }

                }

                break;

            }

        }

    }

    int nRoll;

    if(nRand > 0)

    {

        nRoll = Random(nRand) + 1;

    }

    else

    {

        nRoll = 0;

    }

    //GN_MyPrintString("GENERIC DEBUG *************** Roll = " + GN_ITS(nRoll));

    if(nRand > 0)

    {

        //FRAG GRENADE

        if(nRoll == 1 && n87 == TRUE)

        {

            return tUse = TalentSpell(87);

        }

        if(nRoll > 1 && n87 == TRUE)

        {

            nRoll--;

        }

        //STUN GRENADE

        if(nRoll == 1 && n88 == TRUE)

        {

            return tUse = TalentSpell(88);

        }

        if(nRoll > 1 && n88 == TRUE)

        {

            nRoll--;

        }

        //THERMAL DETONATOR

        if(nRoll == 1 && n89 == TRUE)

        {

            return tUse = TalentSpell(89);

        }

        if(nRoll > 1 && n89 == TRUE)

        {

            nRoll--;

        }

        //POISON

        if(nRoll == 1 && n90 == TRUE)

        {

            return tUse = TalentSpell(90);

        }

        if(nRoll > 1 && n90 == TRUE)

        {

            nRoll--;

        }

        //SONIC

        if(nRoll == 1 && n91 == TRUE)

        {

            return tUse = TalentSpell(91);

        }

        if(nRoll > 1 && n91 == TRUE)

        {

            nRoll--;

        }

        //ADHESIVE

        if(nRoll == 1 && n92 == TRUE)

        {

            return tUse = TalentSpell(92);

        }

        if(nRoll > 1 && n92 == TRUE)

        {

            nRoll--;

        }

        //CRYOBAN

        if(nRoll == 1 && n93 == TRUE)

        {

            return tUse = TalentSpell(93);

        }

        if(nRoll > 1 && n93 == TRUE)

        {

            nRoll--;

        }

        //PLASMA

        if(nRoll == 1 && n94 == TRUE)

        {

            return tUse = TalentSpell(94);

        }

        if(nRoll > 1 && n94 == TRUE)

        {

            nRoll--;

        }

    }

    GN_MyPrintString("GENERIC DEBUG *************** Grenade Selection Failure");

    talent tNull;

    return tNull;

    return tNull;

}



//::///////////////////////////////////////////////

//:: Get Boss Combat Move

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns a talent for the boss to perform

    in combat.  This function will try and pick a

    talent which will inflict maximum damage

    on the party via area of effect spells, grenades

    and debilitating effects.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 2, 2003

//:://////////////////////////////////////////////

talent GN_GetBossCombatMove(int nBossAttackType, int nDroid = FALSE)

{

    talent tInvalid;

    talent tUse;

    int bValid = FALSE;

    if(nBossAttackType == SW_BOSS_ATTACK_TYPE_GRENADE || nBossAttackType == SW_BOSS_ATTACK_ANY)

    {

        tUse = GN_GetGrenadeTalent(nDroid);

        if(GetIsTalentValid(tUse))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Grenade Talent Chosen");

            return tUse;

        }

    }

    if(nBossAttackType == SW_BOSS_ATTACK_TYPE_FORCE_POWER || nBossAttackType == SW_BOSS_ATTACK_ANY)

    {

        tUse = GN_GetAOEForcePower(nDroid);

        if(GetIsTalentValid(tUse))

        {

            GN_MyPrintString("GENERIC DEBUG *************** Boss AI: AOE Force Power Talent Chosen");

            return tUse;

        }

    }

    if(nBossAttackType == SW_BOSS_ATTACK_TYPE_NPC || nBossAttackType == SW_BOSS_ATTACK_ANY)

    {

        if(d100() > 50)

        {

            tUse = GN_GetTargetedForcePower(nDroid);

            if(GetIsTalentValid(tUse))

            {

                GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Targeted Force Power Talent Chosen");

                return tUse;

            }

            tUse = GN_GetAOEForcePower(nDroid);

            if(GetIsTalentValid(tUse))

            {

                GN_MyPrintString("GENERIC DEBUG *************** Boss AI: AOE Force Power Talent Chosen");

                return tUse;

            }

        }

        if(GN_GetWeaponType() == 1)

        {

            GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Melee Feat Talent Chosen");

            tUse = GetCreatureTalentRandom(0x1104); //Only melee feats use this code

        }

        else

        {

            GN_MyPrintString("GENERIC DEBUG *************** Boss AI: Range Feat Talent Chosen");

            tUse = GetCreatureTalentRandom(0x1111); //Only ranged feats use this code

        }

        if(GetIsTalentValid(tUse))

        {

            return tUse;

        }

    }

    else if(nBossAttackType == SW_BOSS_ATTACK_TYPE_PC || nBossAttackType == SW_BOSS_ATTACK_ANY)

    {

        if(d100() > 70)

        {

            tUse = GN_GetTargetedForcePower(nDroid);

            if(GetIsTalentValid(tUse))

            {

                return tUse;

            }

            tUse = GN_GetAOEForcePower(nDroid);

            if(GetIsTalentValid(tUse))

            {

                return tUse;

            }

        }

        tUse = GetCreatureTalentRandom(0x1104); //Only melee feats use this code

        if(GetIsTalentValid(tUse))

        {

            return tUse;

        }

        GN_MyPrintString("GENERIC DEBUG *************** Boss AI: No Feats Available");

    }

    //Comment this out so that the boss AI handles the failure not this function.

    /*

    if(!GetIsTalentValid(tUse) && nBossAttackType != SW_BOSS_ATTACK_ANY)

    {

        tUse = GN_GetBossCombatMove(SW_BOSS_ATTACK_ANY);

    }

    */

    return tUse;

}



//::///////////////////////////////////////////////

//:: Get AOE Force Power

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks and returns a random force power that

    can effect more than 1 target.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 2, 2003

//:://////////////////////////////////////////////

talent GN_GetAOEForcePower(int nDroid = FALSE)

{

    talent tUse;

    int nHorror, nInsanity, nStorm, nWave, nSaber, nLightning, nSleep, nStunDroid, nKillDroid, nHowl, nCnt;



    //MODIFIED by Preston Watamaniuk on April 27, 2003

    //Removed Death Field so that it would be used exlusively for Healing.



    //MODIFIED by Preston Watamaniuk on May 14, 2003

    //Put a check into make sure that the same AOE power is not used over and over.

    int nLastForcePower = GetLastForcePowerUsed(OBJECT_SELF);

    GN_MyPrintString("GENERIC DEBUG *************** Last Force Power Used = " + GN_ITS(nLastForcePower));



    //THIS SECTION DETERMINES WHICH POWERS ARE APPLICABLE

    if(GetHasSpell(FORCE_POWER_HORROR) && nDroid == FALSE && nLastForcePower != FORCE_POWER_HORROR)

    {

        nHorror = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_INSANITY) && nDroid == FALSE && nLastForcePower != FORCE_POWER_INSANITY)

    {

        nInsanity = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_FORCE_STORM) && nLastForcePower != FORCE_POWER_FORCE_STORM)

    {

        nStorm = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_FORCE_WAVE) && nLastForcePower != FORCE_POWER_FORCE_WAVE)

    {

        nWave = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_LIGHT_SABER_THROW_ADVANCED) && nLastForcePower != FORCE_POWER_LIGHT_SABER_THROW_ADVANCED)

    {

        nSaber = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_LIGHTNING) && nLastForcePower != FORCE_POWER_LIGHTNING)

    {

        nLightning = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_SLEEP) && nDroid == FALSE && nLastForcePower != FORCE_POWER_SLEEP)//Now Mass Stasis

    {

        nSleep = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_DROID_STUN) && nDroid == TRUE && nLastForcePower != FORCE_POWER_DROID_STUN)

    {

        nStunDroid = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_DROID_DESTROY) && nDroid == TRUE && nLastForcePower != FORCE_POWER_DROID_DESTROY)

    {

        nKillDroid = 1;

        nCnt++;

    }

    talent tHowl  = TalentSpell(131);

    if(GetCreatureHasTalent(tHowl)) //Sonic Howl

    {

        nHowl = 1;

        nCnt++;

    }



    

    //THIS SECTION DETERMINES WHICH POWER TO USE

    int nRoll;

    if(nCnt > 0)

    {

        nRoll = Random(nCnt) + 1;

    }

    else

    {

        nRoll = 0;

    }

    

    //Horror

    if(nHorror == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_HORROR);

        nRoll--;

    }

    if(nHorror == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Insanity

    if(nInsanity == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_INSANITY);

        nRoll--;

    }

    if(nHorror == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Force Storm

    if(nStorm == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_FORCE_STORM);

        nRoll--;

    }

    if(nStorm == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Force Wave

    if(nWave == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_FORCE_WAVE);

        nRoll--;

    }

    if(nWave == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Advanced Saber Throw

    if(nSaber == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_LIGHT_SABER_THROW_ADVANCED);

        nRoll--;

    }

    if(nSaber == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Lightning

    if(nLightning == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_LIGHTNING);

        nRoll--;

    }

    if(nLightning == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Mass Stasis

    if(nSleep == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_SLEEP);

        nRoll--;

    }

    if(nSleep == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Stun Droid

    if(nStunDroid == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_DROID_STUN);

        nRoll--;

    }

    if(nStunDroid == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Destroy Droid

    if(nKillDroid == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_DROID_DESTROY);

        nRoll--;

    }

    if(nKillDroid == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Sonic Howl

    if(nKillDroid == 1 && nRoll == 1)

    {

        tUse = TalentSpell(131);

        nRoll--;

    }

    if(nHowl == 1 && nRoll > 1)

    {

        nRoll--;

    }

    GN_MyPrintString("GENERIC DEBUG *************** Force Power Returned = " + GN_ITS(GetIdFromTalent(tUse)));

    return tUse;

}



//::///////////////////////////////////////////////

//:: Get Targeted Force Power

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks and returns a random force power that

    can effect 1 target.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 2, 2003

//:://////////////////////////////////////////////

talent GN_GetTargetedForcePower(int nDroid = FALSE)

{

    talent tUse;

    int nChoke, nAfflict, nPlague, nPush, nWind, nLightning, nKill, nHorror, nWound, nStasis, nDroid, nKnock, nHowl, nCnt;



    if(GetRacialType(OBJECT_SELF) == RACIAL_TYPE_DROID)

    {

        tUse = GetCreatureTalentRandom(0x8000);

        if(GetIsTalentValid(tUse))

        {

            return tUse;

        }

    }

    //MODIFIED by Preston Watamaniuk on April 27, 2003

    //Removed Drain Life so that it would be used exlusively for Healing.

    

    if(GetHasSpell(FORCE_POWER_CHOKE) && nDroid == FALSE)

    {

        nChoke = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_AFFLICTION) && nDroid == FALSE)

    {

        nAfflict = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_PLAGUE) && nDroid == FALSE)

    {

        nPlague = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_FORCE_PUSH))

    {

        nPush = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_FORCE_WHIRLWIND))

    {

        nWind = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_LIGHTNING))

    {

        nLightning = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_KILL) && nDroid == FALSE)

    {

        nKill = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_HORROR) && nDroid == FALSE)

    {

        nHorror = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_WOUND) && nDroid == FALSE)

    {

        nWound = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_HOLD))

    {

        nStasis = 1;

        nCnt++;

    }

    if(GetHasSpell(FORCE_POWER_DROID_DISABLE) && nDroid == TRUE)

    {

        nDroid = 1;

        nCnt++;

    }

    talent tSlam  = TalentSpell(83);

    if(GetCreatureHasTalent(tSlam)) //Monster Slam

    {

        nKnock = 1;

        nCnt++;

    }



    //THIS SECTION DETERMINES WHICH POWER TO USE

    int nRoll;

    if(nCnt > 0)

    {

        nRoll = Random(nCnt) + 1;

    }

    else

    {

        nRoll = 0;

    }

    //Choke

    if(nChoke == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_CHOKE);

        nRoll--;

    }

    if(nChoke == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Affliction

    if(nAfflict == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_AFFLICTION);

        nRoll--;

    }

    if(nAfflict == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Plague

    if(nPlague == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_AFFLICTION);

        nRoll--;

    }

    if(nPlague == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Force Push

    if(nPush == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_FORCE_PUSH);

        nRoll--;

    }

    if(nPush == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Force Whirlwind

    if(nWind == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_FORCE_WHIRLWIND);

        nRoll--;

    }

    if(nWind == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Lightning

    if(nLightning == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_LIGHTNING);

        nRoll--;

    }

    if(nLightning == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Kill

    if(nKill == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_KILL);

        nRoll--;

    }

    if(nKill == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Horror

    if(nHorror == 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_HORROR);

        nRoll--;

    }

    if(nHorror == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Wound

    if(nWound== 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_WOUND);

        nRoll--;

    }

    if(nWound == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Stasis

    if(nStasis== 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_HOLD);

        nRoll--;

    }

    if(nStasis == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Disable Droid

    if(nDroid== 1 && nRoll == 1)

    {

        tUse = TalentSpell(FORCE_POWER_DROID_DISABLE);

        nRoll--;

    }

    if(nDroid == 1 && nRoll > 1)

    {

        nRoll--;

    }

    //Monster Slam

    if(nKnock == 1 && nRoll == 1)

    {

        tUse = TalentSpell(83);

        nRoll--;

    }

    if(nKnock == 1 && nRoll > 1)

    {

        nRoll--;

    }

    return tUse;

}



//::///////////////////////////////////////////////

//:: Get Active Party Member Count

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns the number of party members who

    are active

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 2, 2003

//:://////////////////////////////////////////////

int GN_GetActivePartyMemberCount()

{

    object oNPC1 = GetPartyMemberByIndex(0);

    object oNPC2 = GetPartyMemberByIndex(1);

    object oNPC3 = GetPartyMemberByIndex(2);



    int nCnt = 0;



    if(GetIsObjectValid(oNPC1) && GetCurrentHitPoints(oNPC1) > 0 && GetObjectSeen(oNPC1))

    {

        nCnt++;

    }

    if(GetIsObjectValid(oNPC2) && GetCurrentHitPoints(oNPC2) > 0 && GetObjectSeen(oNPC2))

    {

        nCnt++;

    }

    if(GetIsObjectValid(oNPC3) && GetCurrentHitPoints(oNPC3) > 0 && GetObjectSeen(oNPC3))

    {

        nCnt++;

    }

    return nCnt;

}



//::///////////////////////////////////////////////

//:: Get Active Party Member

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns a party member who is active a not

    currently controlled by the PC.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 2, 2003

//:://////////////////////////////////////////////

/*

    MODIFIED by Preston Watamaniuk on March 8, 2003



    Added some functionality so that the Drain Life

    will be targeted on the 0 Index as well as the

    other party members. Also if Drain = TRUE then

    no droids will be returned.

    

    This function will return the nearest non-droid

    enemy if the party is freindly.

*/

//:://////////////////////////////////////////////

object GN_GetActivePartyMember(int nDrainTarget = FALSE)

{

    object oNPC1 = GetPartyMemberByIndex(0);

    object oNPC2 = GetPartyMemberByIndex(1);

    object oNPC3 = GetPartyMemberByIndex(2);

    object oTarget;



    int nCnt = 0;

    int nRoll;

    int nNPC1 = FALSE;

    int nNPC2 = FALSE;

    int nNPC3 = FALSE;



    if(GetIsObjectValid(oNPC2) && GetCurrentHitPoints(oNPC2) > 0 && GetObjectSeen(oNPC2))

    {

        if(GetRacialType(oNPC2) != RACIAL_TYPE_DROID || nDrainTarget == FALSE)

        {

            nCnt++;

            nNPC2 = TRUE;

        }

    }

    if(GetIsObjectValid(oNPC3) && GetCurrentHitPoints(oNPC3) > 0 && GetObjectSeen(oNPC3))

    {

        if(GetRacialType(oNPC3) != RACIAL_TYPE_DROID || nDrainTarget == FALSE)

        {

            nCnt++;

            nNPC3 = TRUE;

        }

    }



    if(nDrainTarget == TRUE)

    {

        if(GetIsObjectValid(oNPC1) && GetCurrentHitPoints(oNPC1) > 0 && GetObjectSeen(oNPC1))

        {

            if(GetRacialType(oNPC1) != RACIAL_TYPE_DROID)

            {

                nCnt++;

                nNPC1 = TRUE;

            }

        }

    }



    if(nCnt == 0)

    {

        oTarget = OBJECT_INVALID;

    }

    else if(nCnt == 1)

    {

        if(nNPC2 == TRUE){oTarget = oNPC2;}

        else if(nNPC3 == TRUE){oTarget = oNPC3;}

        else if(nNPC1 == TRUE){oTarget = oNPC1;}

    }

    else if(nCnt == 2)

    {

        nRoll = d100();

        if(nNPC1 == TRUE && nNPC2 == TRUE)

        {

            if(nRoll > 50){oTarget = oNPC1;}

            else{oTarget = oNPC2;}

        }

        else if(nNPC1 == TRUE && nNPC3 == TRUE)

        {

            if(nRoll > 50){oTarget = oNPC1;}

            else{oTarget = oNPC3;}

        }

        else if(nNPC2 == TRUE && nNPC3 == TRUE)

        {

            if(nRoll > 50){oTarget = oNPC2;}

            else{oTarget = oNPC3;}

        }

    }

    else if(nCnt == 3)

    {

        nRoll = d100();

        if(nRoll <= 33){oTarget = oNPC1;}

        else if(nRoll > 33 && nRoll <= 66) {oTarget = oNPC2;}

        else if(nRoll > 66 && nRoll <= 100) {oTarget = oNPC3;}

    }

    

    //MODIFIED by Preston Watamaniuk on May 18, 2003

    //Changed the racial type to Human from Droid.

    if(!GetIsEnemy(oTarget, OBJECT_SELF) && nDrainTarget == TRUE)

    {

        GN_MyPrintString("GENERIC DEBUG *************** Searching for Alternate Target");

        oTarget = GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, OBJECT_SELF, 1, CREATURE_TYPE_RACIAL_TYPE, RACIAL_TYPE_HUMAN);

        GN_MyPrintString("GENERIC DEBUG *************** Alternate Target = " + GN_ReturnDebugName(oTarget));

    }

    GN_MyPrintString("GENERIC DEBUG *************** Heal Drain Target = " + GN_ITS(nDrainTarget));

    GN_MyPrintString("GENERIC DEBUG *************** Get Active Party Member: " + GN_ReturnDebugName(oTarget));

    return oTarget;

}



//::///////////////////////////////////////////////

//:: Return Active Party Member

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This function returns an active party member.

    They must not be dead.  The debilitated

    parameter will ignore those party members

    already debilitated.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: June 12, 2003

//:://////////////////////////////////////////////

object GN_ReturnActivePartyMember(int nDebil = FALSE)

{

    object oNPC1 = GetPartyMemberByIndex(0);

    object oNPC2 = GetPartyMemberByIndex(1);

    object oNPC3 = GetPartyMemberByIndex(2);

    object oTarget;



    int nCnt = 0;

    int nRoll;

    int nNPC1 = FALSE;

    int nNPC2 = FALSE;

    int nNPC3 = FALSE;



    if(GetIsObjectValid(oNPC2) && GetCurrentHitPoints(oNPC2) > 0 && GetObjectSeen(oNPC2))

    {

        if(nDebil == FALSE || !GetIsDebilitated(oNPC2))

        {

            nCnt++;

            nNPC2 = TRUE;

        }

    }

    if(GetIsObjectValid(oNPC3) && GetCurrentHitPoints(oNPC3) > 0 && GetObjectSeen(oNPC3))

    {

        if(nDebil == FALSE || !GetIsDebilitated(oNPC2))

        {

            nCnt++;

            nNPC3 = TRUE;

        }

    }



    if(GetIsObjectValid(oNPC1) && GetCurrentHitPoints(oNPC1) > 0 && GetObjectSeen(oNPC1))

    {

        if(nDebil == FALSE || !GetIsDebilitated(oNPC2))

        {

            nCnt++;

            nNPC1 = TRUE;

        }

    }

    if(nCnt == 0)

    {

        oTarget = OBJECT_INVALID;

    }

    else if(nCnt == 1)

    {

        if(nNPC2 == TRUE){oTarget = oNPC2;}

        else if(nNPC3 == TRUE){oTarget = oNPC3;}

        else if(nNPC1 == TRUE){oTarget = oNPC1;}

    }

    else if(nCnt == 2)

    {

        nRoll = d100();

        if(nNPC1 == TRUE && nNPC2 == TRUE)

        {

            if(nRoll > 50){oTarget = oNPC1;}

            else{oTarget = oNPC2;}

        }

        else if(nNPC1 == TRUE && nNPC3 == TRUE)

        {

            if(nRoll > 50){oTarget = oNPC1;}

            else{oTarget = oNPC3;}

        }

        else if(nNPC2 == TRUE && nNPC3 == TRUE)

        {

            if(nRoll > 50){oTarget = oNPC2;}

            else{oTarget = oNPC3;}

        }

    }

    else if(nCnt == 3)

    {

        nRoll = d100();

        if(nRoll <= 33){oTarget = oNPC1;}

        else if(nRoll > 33 && nRoll <= 66) {oTarget = oNPC2;}

        else if(nRoll > 66 && nRoll <= 100) {oTarget = oNPC3;}

    }

    

    return oTarget;

}



//:://///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//:: Generic Include Debug Commands

//:: Copyright (c) 2001 Bioware Corp.

//::////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//::////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: June 12, 2002

//::////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



void GN_MySpeakString(string sString)

{

    //SpeakString(sString);

}



void GN_AssignPCDebugString(string sString)

{

    object oPC = GetNearestCreature(CREATURE_TYPE_PLAYER_CHAR, PLAYER_CHAR_IS_PC);

    if(GetIsObjectValid(oPC))

    {

        AssignCommand(oPC, SpeakString(sString));

    }

}

void GN_PostString(string sString = "",int x = 10,int y = 10,float fShow = 4.0)

{

    //AurPostString(sString,x,y,fShow);

}



void GN_MyPrintString(string sString)

{

    if(!ShipBuild())

    {

        PrintString(sString);

    }

}



void GN_PostShoutString(string sString = "",int x = 10,int y = 10,float fShow = 4.0)

{

    //AurPostString(sString,x,y,fShow);

}



void GN_MyPrintShoutString(string sString)

{

    if(!ShipBuild())

    {

        //PrintString(sString);

    }

}





void GN_PrintShoutType(object oShouter, int nShout)

{

    /*

    //I WAS ATTACKED

    if(nShout == 1)

    {

        GN_MyPrintString("GENERIC DEBUG *************** " + GetName(oShouter) + "/" + ObjectToString(oShouter) + " ATTACKED");

    }

    //I WAS KILLED

    else if(nShout == 3)

    {

        GN_MyPrintString("GENERIC DEBUG *************** " + GetName(oShouter) + "/" + ObjectToString(oShouter) + " KILLED");

    }

    //CALL TO ARMS

    else if(nShout == 6)

    {

        GN_MyPrintString("GENERIC DEBUG *************** " + GetName(oShouter) + "/" + ObjectToString(oShouter) + " CALL TO ARMS");

    }

    //SUPRESS FORCE

    else if(nShout == 9)

    {

        GN_MyPrintString("GENERIC DEBUG *************** " + GetName(oShouter) + "/" + ObjectToString(oShouter) + " WANTS FORCE SUPPRESSED");

    }

    //FLEE FROM GRENADES

    else if(nShout == 12)

    {

        GN_MyPrintString("GENERIC DEBUG *************** " + GetName(oShouter) + "/" + ObjectToString(oShouter) + " GRENADE THROWN");

    }

    //I SEE AN ENEMY

    else if(nShout == 15)

    {

        GN_MyPrintString("GENERIC DEBUG *************** " + GetName(oShouter) + "/" + ObjectToString(oShouter) + " SEES AN ENEMY");

    }

    */

}



string GN_ReturnDebugName(object oTarget)

{

    string sName = GetName(oTarget) + "_" + ObjectToString(oTarget);

    return sName;

}



string GN_FetchComboString(int nCombo)

{

    if(nCombo == SW_COMBO_RANGED_FEROCIOUS){return "SW_COMBO_RANGED_FEROCIOUS";}

    else if(nCombo == SW_COMBO_RANGED_AGGRESSIVE){return "SW_COMBO_RANGED_AGGRESSIVE";}

    else if(nCombo == SW_COMBO_RANGED_DISCIPLINED){return "SW_COMBO_RANGED_DISCIPLINED";}

    else if(nCombo == SW_COMBO_RANGED_CAUTIOUS){return "SW_COMBO_RANGED_CAUTIOUS";}

    else if(nCombo == SW_COMBO_MELEE_FEROCIOUS){return "SW_COMBO_MELEE_FEROCIOUS";}

    else if(nCombo == SW_COMBO_MELEE_AGGRESSIVE){return "SW_COMBO_MELEE_AGGRESSIVE";}

    else if(nCombo == SW_COMBO_MELEE_DISCIPLINED){return "SW_COMBO_MELEE_DISCIPLINED";}

    else if(nCombo == SW_COMBO_MELEE_CAUTIOUS){return "SW_COMBO_MELEE_CAUTIOUS";}

    else if(nCombo == SW_COMBO_BUFF_PARTY){return "SW_COMBO_BUFF_PARTY";}

    else if(nCombo == SW_COMBO_BUFF_DEBILITATE){return "SW_COMBO_BUFF_DEBILITATE";}

    else if(nCombo == SW_COMBO_BUFF_DAMAGE){return "SW_COMBO_BUFF_DAMAGE";}

    else if(nCombo == SW_COMBO_BUFF_DEBILITATE_DESTROY){return "SW_COMBO_BUFF_DEBILITATE_DESTROY";}

    else if(nCombo == SW_COMBO_SUPRESS_DEBILITATE_DESTROY){return "SW_COMBO_SUPRESS_DEBILITATE_DESTROY";}

    else if(nCombo == SW_COMBO_SITH_ATTACK){return "SW_COMBO_SITH_ATTACK";}

    else if(nCombo == SW_COMBO_BUFF_ATTACK){return "SW_COMBO_BUFF_ATTACK";}

    else if(nCombo == SW_COMBO_SITH_CONFOUND){return "SW_COMBO_SITH_CONFOUND";}

    else if(nCombo == SW_COMBO_JEDI_SMITE){return "SW_COMBO_JEDI_SMITE";}

    else if(nCombo == SW_COMBO_SITH_TAUNT){return "SW_COMBO_SITH_TAUNT";}

    else if(nCombo == SW_COMBO_SITH_BLADE){return "SW_COMBO_SITH_BLADE";}

    else if(nCombo == SW_COMBO_SITH_CRUSH){return "SW_COMBO_SITH_CRUSH";}

    else if(nCombo == SW_COMBO_JEDI_CRUSH){return "SW_COMBO_JEDI_CRUSH";}

    else if(nCombo == SW_COMBO_SITH_BRUTALIZE){return "SW_COMBO_SITH_BRUTALIZE";}

    else if(nCombo == SW_COMBO_SITH_DRAIN){return "SW_COMBO_SITH_DRAIN";}

    else if(nCombo == SW_COMBO_SITH_ESCAPE){return "SW_COMBO_SITH_ESCAPE";}

    else if(nCombo == SW_COMBO_JEDI_BLITZ){return "SW_COMBO_JEDI_BLITZ";}

    else if(nCombo == SW_COMBO_SITH_SPIKE){return "SW_COMBO_SITH_SPIKE";}

    else if(nCombo == SW_COMBO_SITH_SCYTHE){return "SW_COMBO_SITH_SCYTHE";}

    else if(nCombo == SW_COMBO_DROID_UTILITIES){return "SW_COMBO_DROID_UTILITIES";}

    return "NO COMBO SELECTED";

}





//::///////////////////////////////////////////////

//:: Return AI Style

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns the AI style in a string

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 28, 2003

//:://////////////////////////////////////////////



string GN_ReturnAIStyle(object oTarget = OBJECT_SELF)

{

    if(GetNPCAIStyle(oTarget) == NPC_AISTYLE_AID)

    {

        return "NPC_AISTYLE_AID";

    }

    else if(GetNPCAIStyle(oTarget) == NPC_AISTYLE_GRENADE_THROWER)

    {

        return "NPC_AISTYLE_GRENADE_THROWER";

    }

    else if(GetNPCAIStyle(oTarget) == NPC_AISTYLE_JEDI_SUPPORT)

    {

        return "NPC_AISTYLE_JEDI_SUPPORT";

    }

    else if(GetNPCAIStyle(oTarget) == NPC_AISTYLE_DEFAULT_ATTACK)

    {

        return "NPC_AISTYLE_DEFAULT_ATTACK";

    }

    int nAI = GetNPCAIStyle(oTarget);

    string sAI = IntToString(nAI);

    sAI = "No Valid AI Set, state = " + sAI;

    return sAI;

}



string GN_ITS(int sFutureString)

{

    return IntToString(sFutureString);

}



''',

    'k_inc_kas': b'''//::///////////////////////////////////////////////

//:: Include

//:: k_inc_kas

//:: Copyright (c) 2002 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This is the include file for Kashyyyk.

*/

//:://////////////////////////////////////////////

//:: Created By: John Winski

//:: Created On: July 29, 2002

//:://////////////////////////////////////////////

#include "k_inc_utility"

#include "k_inc_generic"



int GetGorwookenSpawnGlobal()

{

    return GetGlobalBoolean("kas_SpawnGorwook");

}



void SetGorwookenSpawnGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_SpawnGorwook", bValue);

    }



    return;

}



int GetEliBeenKilledGlobal()

{

    return GetGlobalBoolean("kas_elikilled");

}



void SetEliBeenKilledGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_elikilled", bValue);

    }



    return;

}



int GetJaarakConfessedGlobal()

{

    return GetGlobalBoolean("kas_JaarakConfessed");

}



void SetJaarakConfessedGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_JaarakConfessed", bValue);

    }



    return;

}



int GetKashyyykPazaakStateGlobal()

{

    return GetGlobalNumber("tat_kashpazstate");

}



void SetKashyyykPazaakStateGlobal(int bValue)

{

    SetGlobalNumber("tat_kashpazstate", bValue);



    return;

}



int GetGuardToldGlobal()

{

    return GetGlobalBoolean("kas_GuardTold");

}



void SetGuardToldGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_GuardTold", bValue);

    }



    return;

}



int GetPoacherPlotStateGlobal()

{

return GetGlobalNumber("kas_poacherstate");

}



void SetPoacherPlotStateGlobal(int bValue)

{

SetGlobalNumber("kas_poacherstate", bValue);

return;

}





int GetPlayerToldOfPoachersGlobal()

{

    return GetGlobalBoolean("kas_ToldPoachers");

}



void SetPlayerToldOfPoachersGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_ToldPoachers", bValue);

    }



    return;

}



int GetChuundarTalkGlobal()

{

    return GetGlobalBoolean("kas_TalkChuundar");

}



void SetChuundarTalkGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_TalkChuundar", bValue);

    }



    return;

}



int GetHelpedFreyyrGlobal()

{

    return GetGlobalBoolean("kas_HelpedFreyyr");

}



void SetHelpedFreyyrGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_HelpedFreyyr", bValue);

    }



    return;

}



int GetFreyyrDeadGlobal()

{

	return GetGlobalBoolean("kas_FreyyrDead");

}



void SetFreyyrDeadGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_FreyyrDead", bValue);

    }



    return;

}



int GetChuundarDeadGlobal()

{

	return GetGlobalBoolean("kas_ChuundarDead");

}



void SetChuundarDeadGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_ChuundarDead", bValue);

    }



    return;

}



int GetComputerTalkGlobal()

{

    return GetGlobalBoolean("kas_ComputerTalk");

}



void SetComputerTalkGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_ComputerTalk", bValue);

    }



    return;

}



int GetStarMapRecievedGlobal()

{

    return GetGlobalBoolean("kas_StarMap");

}



void SetStarMapRecievedGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_StarMap", bValue);

    }



    return;

}



int GetJaarakBoltsGlobal()

{

    return GetGlobalBoolean("kas_JaarakBolts");

}



void SetJaarakBoltsGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_JaarakBolts", bValue);

    }



    return;

}



int GetJaarakDeadGlobal()

{

    return GetGlobalBoolean("kas_JaarakDead");

}



void SetJaarakDeadGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_JaarakDead", bValue);

    }



    return;

}



int GetJaarakFreeGlobal()

{

    return GetGlobalBoolean("kas_JaarakFree");

}



void SetJaarakFreeGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_JaarakFree", bValue);

    }



    return;

}



int GetRorworrMissingGlobal()

{

    return GetGlobalBoolean("kas_RorworrMiss");

}



void SetRorworrMissingGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_RorworrMiss", bValue);

    }



    return;

}



int GetDroidTalkGlobal()

{

    return GetGlobalBoolean("kas_DroidTalk");

}



void SetDroidTalkGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_DroidTalk", bValue);

    }



    return;

}



int GetChuundarRewardGlobal()

{

    return GetGlobalBoolean("kas_ChuundReward");

}



void SetChuundarRewardGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_ChuundReward", bValue);

    }



    return;

}



int GetMandalorianPlotGlobal()

{

    return GetGlobalNumber("kas_MandalorPlot");

}



void SetMandalorianPlotGlobal(int bValue)

{

    SetGlobalNumber("kas_MandalorPlot", bValue);



    return;

}



int GetAskedJanosForRewardLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for xxJanos.02 in area kas_m22aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01);

}



void SetAskedJanosForRewardLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for xxJanos.02 in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetJanosPaidLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for Janos in area kas_m22aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01);

}



void SetJanosPaidLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for Janos in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetJanosOfficeLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for Janos in area kas_m22aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_02);

}



void SetJanosOfficeLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for Janos in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetPlayerAskedAboutSlavesLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_03 for Janos in area kas_m22aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_03);

}



void SetPlayerAskedAboutSlavesLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_03 for Janos in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetPlayerAskedAboutSuppliesLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_04 for Janos in area kas_m22aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_04);

}



void SetPlayerAskedAboutSuppliesLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_04 for Janos in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetJoleeHomeLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for area kas_m24aa.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01);

}



void SetJoleeHomeLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetJoleeInfoLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for area kas_m24aa.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_02);

}



void SetJoleeInfoLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetPoachersRunoffLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_03 for the area kas_m24aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_03);

}



void SetPoachersRunoffLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_03 for the area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetPoachersKilledLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_04 for the area kas_m24aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_04);

}



void SetPoachersKilledLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_04 for the area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetForceFieldLocal()

{

    // This uses SW_PLOT_BOOLEAN_05 for area kas_m24aa.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_05);

}



void SetForceFieldLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_05 for area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetOpenForceFieldLocal()

{

    // This uses SW_PLOT_BOOLEAN_06 for area kas_m24aa.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_06);

}



void SetOpenForceFieldLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_06 for area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_06, bValue);

    }



    return;

}



int GetForceFieldInfoLocal()

{

    // This uses SW_PLOT_BOOLEAN_07 for area kas_m24aa.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_07);

}



void SetForceFieldInfoLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_07 for area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_07, bValue);

    }



    return;

}



int GetEnteredShadowlandsLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_08 for area kas_m24aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_08);

}



void SetEnteredShadowlandsLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_08 for area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_08, bValue);

    }



    return;

}



int GetJoleeTalkLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_09 for area kas_m24aa.



	return UT_GetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_09);

}



void SetJoleeTalkLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_09 for area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_09, bValue);

    }



    return;

}



int GetUllerBerriesLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the uller.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetUllerBerriesLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the uller.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetFreyyrSpawnGlobal()

{

    // This uses SW_PLOT_BOOLEAN_01 for area kas_m23ad.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01);

}



void SetFreyyrSpawnGlobal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for area kas_m23ad.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetFreyyrBeatLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Freyyr in area kas_m25aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetFreyyrBeatLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Freyyr in area kas_m25aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetComputerShutdownLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the computer in area kas_m25aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetComputerShutdownLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the computer in area kas_m25aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetRecognizedRevanLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for the computer in area kas_m25aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetRecognizedRevanLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for the computer in area kas_m25aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetComputerAttackLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for the computer in area kas_m25aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetComputerAttackLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for the computer in area kas_m25aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetHealChanceLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Grrrwahrr in area kas_m25aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetHealChanceLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Grrrwahrr in area kas_m25aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetEvilHurtLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Grrrwahrr in area kas_m25aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetEvilHurtLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Grrrwahrr in area kas_m25aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetFreyyrMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Freyyr in area kas_m23ad.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetFreyyrMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Freyyr in area kas_m23ad.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetZaalbarMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for area kas_m23ad.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_02);

}



void SetZaalbarMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for area kas_m23ad.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetAskAboutComputerLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for area kas_m23ad.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_03);

}



void SetAskAboutComputerLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for area kas_m23ad.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetFreyyrUpsetLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for area kas_m23ad.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_04);

}



void SetFreyyrUpsetLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for area kas_m23ad.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetFinalBattleLocal()

{

    // This uses SW_PLOT_BOOLEAN_05 for area kas_m23ad.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_05);

}



void SetFinalBattleLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_05 for area kas_m23ad.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetFadeOffLocal()

{

    // This uses SW_PLOT_BOOLEAN_06 for area kas_m23ad.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_06);

}



void SetFadeOffLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_06 for area kas_m23ad.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_06, bValue);

    }



    return;

}



int GetJaarakTrialLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for area kas_m23ac.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01);

}



void SetJaarakTrialLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for area kas_m23ac.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetJaarakAngeredOnceLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Woorwill in area kas_m23ab.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetJaarakAngeredOnceLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the computer in area kas_m23ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetRorworrDescribedOnceLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Woorwill in area kas_m23ab.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetRorworrDescribedOnceLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for the computer in area kas_m23ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetRorworrGoneSinceLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Woorwill in area kas_m23ab.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetRorworrGoneSinceLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for the computer in area kas_m23ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetJaarakAccusedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for area kas_m23ab.



	return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01);

}



void SetJaarakAccusedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for area kas_m23ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetPoachersDeadGlobal()

{

	return GetGlobalNumber("kas_PoachersDead");

}



void SetPoachersDeadGlobal(int bValue)

{

    SetGlobalNumber("kas_PoachersDead", bValue);



    return;

}



int GetEmittersOffGlobal()

{

	return GetGlobalNumber("kas_EmittersOff");

}



void SetEmittersOffGlobal(int bValue)

{

    SetGlobalNumber("kas_EmittersOff", bValue);



    return;

}



int GetPoacherJobLocal()

{

	// This was changed from a local to a global because I needed to turn

	// all tach in kas_m24aa and kas_m25aa hostile.



    return GetGlobalBoolean("kas_PoacherJob");

}



void SetPoacherJobLocal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("kas_PoacherJob", bValue);

    }



    return;

}



int GetPoacherThreatenLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the officer in area kas_m24aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetPoacherThreatenLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the officer in area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetPoacherRunLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for the officer in area kas_m24aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_02);

}



void SetPoacherRunLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for the officer in area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetPoacherAlarmLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for each guard in area kas_m24aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01);

}



void SetPoacherAlarmLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for each guard in area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetDesertLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for each guard in area kas_m24aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_02);

}



void SetDesertLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for each guard in area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetDroidNorthLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the busted droid in area kas_m24aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetDroidNorthLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the busted droid in area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetGuardThreatenedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the guard at the exit to area kas_m22aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetGuardThreatenedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the guard at the exit to area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetScientistThreatenedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the sceintist in area kas_m22aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetScientistThreatenedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the sceintist in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}





int GetDroidSouthLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for the busted droid in area kas_m24aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetDroidSouthLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for the busted droid in area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetWorrroznorRewardLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Worrroznor in area kas_m23ac.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetWorrroznorRewardLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Worrroznor in area kas_m23ac.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetKashyyykPazaakPlayedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Pazzak on alien player in the area kas_m22aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetKashyyykPazaakPlayedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Pazzak on alien player in the area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetKashyyykLostLastGameLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Pazzak on alien player in the area kas_m22aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetKashyyykLostLastGameLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Pazzak on alien player in the area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetToldOfKashyyykPazaakLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Pazzak on alien player in the area kas_m22aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetToldOfKashyyykPazaakLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for Pazzak on alien player in the area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetAskDehnoLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Captain Dehno in area kas_m22ab.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetAskDehnoLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Captain Dehno in area kas_m22ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetDehnoPaidLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Captain Dehno in area kas_m22ab.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetDehnoPaidLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Captain Dehno in area kas_m22ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetChorrawlMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Chorrawl in area kas_m22ab.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetChorrawlMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Chorrawl in area kas_m22ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetDroidShutdownLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the supply droid in area kas_m22ab.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetDroidShutdownLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the supply droid in area kas_m22ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetEliSaidKoltoLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for the Eli in area kas_m22aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetEliSaidKoltoLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for the Eli in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetEliSaidKorribanLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for the Eli in area kas_m22aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetEliSaidKorribanLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_03 for the Eli in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetEliSaidSwoopLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for the Eli in area kas_m22aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04);

}



void SetEliSaidSwoopLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_04 for the Eli in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetEliDeadLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the Matton Dasol in area kas_m22aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetEliDeadLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the Matton Dasol in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetMattonShopLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for the Matton Dasol in area kas_m22aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetMattonShopLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for the Matton Dasol in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetWookieeGuardZaalbarLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for the wookiee guard in area kas_m22ab.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetWookieeGuardZaalbarLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for the wookiee guard in area kas_m22ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}





int GetMattonGaveReward()

{

    // This uses SW_PLOT_BOOLEAN_03 for the Matton Dasol in area kas_m22aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetMattonGaveReward(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for the Matton Dasol in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetMattonLeaveShopLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for the Matton Dasol in area kas_m22aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04);

}



void SetMattonLeaveShopLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for the Matton Dasol in area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetEmitterShutdown()

{

    // This uses SW_PLOT_BOOLEAN_01 for the emitters in area kas_m24aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetEmitterShutdown(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the emitters in area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetEmitterDamagedLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for the emitters in area kas_m24aa.



	return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetEmitterDamagedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for the emitters in area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetForceFieldOpenLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_10 for the forcefield in area kas_m24aa.



	return UT_GetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_10);

}



void SetForceFieldOpenLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_10 for the forcefield in area kas_m24aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_10, bValue);

    }



    return;

}



int GetWookieHealedLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area kas_m25aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01);

}



void SetWookieHealedLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area kas_m25aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetAngryTachLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for the area kas_m25aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_02);

}



void SetAngryTachLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for the area kas_m25aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetFreyyrJobLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_03 for the area kas_m25aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_03);

}



void SetFreyyrJobLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_03 for the area kas_m25aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetZaalbarTalk1Local(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area kas_m22aa.



	return UT_GetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_01);

}



void SetZaalbarTalk1Local(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetPartyTalk1Local(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for the area kas_m22aa.



	return UT_GetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_02);

}



void SetPartyTalk1Local(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for the area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetWookieRebelsLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_03 for the area kas_m22aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_03);

}



void SetWookieRebelsLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_03 for the area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}





int GetWookieCapturedLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_04 for the area kas_m22aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_04);

}



void SetWookieCapturedLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_04 for the area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetKomadSpawnLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_05 for the area kas_m22aa.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_05);

}



void SetKomadSpawnLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_05 for the area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetRebelFight1Local(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_06 for the area kas_m22aa.



	return UT_GetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_06);

}



void SetRebelFight1Local(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_06 for the area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_06, bValue);

    }



    return;

}



int GetRebelFight2Local(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_07 for the area kas_m22aa.



	return UT_GetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_07);

}



void SetRebelFight2Local(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_07 for the area kas_m22aa.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_07, bValue);

    }



    return;

}



int GetZaalbarTalk2Local(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area kas_m22ab.



	return UT_GetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_01);

}



void SetZaalbarTalk2Local(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area kas_m22ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetPartyTalk2Local(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for the area kas_m22ab.



	return UT_GetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_02);

}



void SetPartyTalk2Local(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for the area kas_m22ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetWookieRebels2Local(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_03 for the area kas_m22ab.



	return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_03);

}



void SetWookieRebels2Local(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_03 for the area kas_m22ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetChorrawlFightLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_04 for the area kas_m22ab.



	return UT_GetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_04);

}



void SetChorrawlFightLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_04 for the area kas_m22ab.



    if (bValue == TRUE || bValue == FALSE)

    {

		UT_SetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}''',

    'k_inc_lev': b'''//::///////////////////////////////////////////////

//:: k_inc_lev

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

  include file for leviathan

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 26, 2002

//:://////////////////////////////////////////////

#include "k_inc_debug"

#include "k_inc_utility"

//mark an object for cleanup by the LEV_CleanupDeadObjects function

void LEV_MarkForCleanup(object obj);



//destroy all objects whose PLOT_10 flag has been set

void LEV_CleanupDeadObjects(object oArea);



//mark object for cleanup and move to nearest exit

void LEV_LeaveArea(object obj = OBJECT_SELF, int bRun = FALSE);



//fill container with treasure from table

void LEV_AddTreasureToContainer(object oContainer,int iTable,int iAmount);



//strip inventory from oTarget and put it in oDest

void LEV_StripCharacter(object oTarget,object oDest);



//::///////////////////////////////////////////////

//:: LEV_MarkForCleanup

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//mark an object for cleanup by the TAR_CleanupDeadObjects function

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 26, 2002

//:://////////////////////////////////////////////

void LEV_MarkForCleanup(object obj)

{

  UT_SetPlotBooleanFlag(obj,SW_PLOT_BOOLEAN_10,TRUE);

}



//::///////////////////////////////////////////////

//:: LEV_CleanupDeadObjects

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//destroy all objects whose PLOT_10 flag has been set

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 15, 2002

//:://////////////////////////////////////////////

void LEV_CleanupDeadObjects(object oArea)

{

  object obj;



  obj = GetFirstObjectInArea(oArea);

  //Db_PostString("START CLEANUP...",5,7,5.0);

  while(GetIsObjectValid(obj))

  {

    //Db_PostString("FOUND OBJ",5,6,5.0);

    if(UT_GetPlotBooleanFlag(obj,SW_PLOT_BOOLEAN_10))

    {

      //Db_PostString("CLEANING UP OBJECT",5,5,5.0);

      DestroyObject(obj);

    }

    obj = GetNextObjectInArea(oArea);

  }

}



//::///////////////////////////////////////////////

//:: LEV_LeaveArea

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//mark object for cleanup and move to nearest exit

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 26, 2002

//:://////////////////////////////////////////////

void LEV_LeaveArea(object obj = OBJECT_SELF, int bRun = FALSE)

{

  object oExit = GetNearestObjectByTag("plev_wpnpcext");



  LEV_MarkForCleanup(obj);

  if(GetIsObjectValid(oExit))

  {

    UT_PlotMoveObject(oExit,bRun);

  }

}



//fill container with treasure from table

void LEV_AddTreasureToContainer(object oContainer,int iTable,int iAmount)

{

  int i;



  if(!GetIsObjectValid(oContainer))

  {

    return;

  }



  for(i = 0;i < iAmount;i++)

  {

    switch(iTable)

    {

    case 0:

      switch(Random(3))

      {

      case 0:

        CreateItemOnObject("G_I_CREDITS001",oContainer,Random(30) + 10);

        break;

      case 1:

        CreateItemOnObject("G_I_DRDREPEQP002",oContainer);

        break;

      case 2:

        CreateItemOnObject("G_I_MEDEQPMNT04",oContainer);

        break;

      default:

        CreateItemOnObject("G_I_MEDEQPMNT02",oContainer);

      }

      break;

    }

  }

}



void LEV_StripCharacter(object oTarget,object oDest)

{

  object oItem;



  if(!GetIsObjectValid(oTarget) || !GetIsObjectValid(oDest))

  {

    return;

  }

  

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_BELT,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_BODY,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_HANDS,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_HEAD,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_IMPLANT,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_LEFTARM,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_LEFTWEAPON,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_RIGHTARM,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_RIGHTWEAPON,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  

  oItem = GetFirstItemInInventory(oTarget);

  while(GetIsObjectValid(oItem))

  {

    GiveItem(oItem,oDest);

    oItem = GetFirstItemInInventory(oTarget);

  }

}

''',

    'k_inc_man': b'''//:: Name

/*

     Desc

*/

//:: Created By:

//:: Copyright (c) 2002 Bioware Corp.



#include "k_inc_generic"

#include "k_inc_utility"



int SHIP_TAKEOFF_CUTSCENE = 1;

int SHIP_LANDING_CUTSCENE = 2;

int NONE = 0;

int QUEEDLE = 1;

int CASSANDRA = 2;

int JAX = 3;

int QUEEDLE_CHAMP = 4;



int QUEEDLE_TIME = 3012;

int CASSANDRA_TIME = 2702;

int JAX_TIME = 2548;

int CHAMP_TIME = 2348;



int PLOT_HARVEST_STOPPED = 3;

int PLOT_KOLTO_DESTROYED = 4;



//effect EFFECT_STEAM = EffectDamage(15);

int STEAM_DAMAGE_AMOUNT = 25;

string RACE_DEFAULT = GetStringByStrRef(32289);

string STEAM_PLACEABLE = "man27_visstm0";

string ROLAND_TAG = "man26_repdip";

void PlaceShip(string sTag,location lLoc);



void RemoveShip(string sTag);



void PlaceNPC(string sTag);



// switches current player models to envirosuit models.

void DonSuits();



// switches the envirosuit model back to the regular player models

void RemoveSuits();



// deactivates all turrets on the map with the corresponding tag

// if no tag is given it will default to the tag of the calling object

void DeactivateTurrets(string sTag = "");



//used to make a given condition only fire once

//***note uses SW_PLOT_BOOLEAN_10***

int HasNeverTriggered();



// Sets a global to track who the player is racing

void SetOpponent(int nOpponent);



//Returns thte current race opponent

int GetOpponent();



//Sets a cutom token in racetime format

void SetTokenRaceTime(int nToken, int nRacerTime);



//returns the main plot global for Manaan

int GetManaanMainPlotVariable();



// returns true if poison has been released if the Hrakert rift

int KoltoDestroyed();



// Removes instances and deactives Selkath encounters

void ClearSelkathFromThisLevel();



// Opens the water door based on the tag og the button

void OpenAssociatedDoor();



// Closes the water door based on the tag og the button

void CloseAssociatedDoor();



// returns the state of a water room TRUE == full

int GetRoomFull(string sRoom);



// sets the water room to nValue

void SetRoomFull(string sRoom, int nValue);



// CLoses all water doors

void CloseAllWaterDoors();



//checks if there is water on either side of the door, if not the door opens

void OpenWaterDoor(string sRoom1,string sRoom2 = "");



//switches water filled rooms accross the corridor

void SwitchWaterRooms();



//returns True if the steam vent is active

int GetIsVentActive(object oVent = OBJECT_SELF);



//sets the state of the Vent and playes the appropriate animation

void SetVentActive(int bState,object oVent = OBJECT_SELF);



// Gives the correct readout for the various water displays

void ActivateWaterDisplays(string sRoom,int nValue);



//plays the required looping animation for the injecter display

void PlayInjecterAnimation(int nLevel);



//plays the required looping animation for the container display

void PlayContainerAnimation(int nLevel);



//initates the sitting animations for the sitting placeables

void InitiateSitters();



// returns true if the staramp was found on Manaan

int GetManaanStarMapFound();



//Turns off AI on party members (if any) for curscene purposes

void TurnOffPartyAI();



//Turns on AI on party members (if any)

void TurnOnPartyAI();



//roland is in post plot state uses SW_PLOT_BOOLEAN05

int GetRolandIsPostPlot();



//toggles the post plot state of Roland

void SetRolandIsPostPlot(int nValue);



//returns the plot global for the missing Selkath youth plot

//used primarily by Shealas(manm26ab) and Sasha (man27aa)

int GetMissingSelkathPlotVariable();



//Sets the plot global for the missing Selkath youth plot

//used primarily by Shealas(manm26ab) and Sasha (man27aa)

void SetMissingSelkathPlotVariable(int nValue);



// returns true if Sasha has been killed

int GetIsSashaDead();



// Sets the variable tracking wheather Sasha is alive

void SetIsSashaDead();

////////////////////////////////////////////////////////////////////////////////

void RemoveShip(string sTag)

{

    object oShip = GetObjectByTag(sTag);

    if(GetIsObjectValid(oShip))

    {

        DestroyObject(oShip);

    }

}



void PlaceShip(string sTag,location lLoc)

{

    object oShip = GetObjectByTag(sTag);

    if(GetIsObjectValid(oShip) == FALSE)

    {

        CreateObject(OBJECT_TYPE_PLACEABLE,sTag,lLoc);

    }

}



void PlaceNPC(string sTag)

{

    if(!GetIsObjectValid(GetObjectByTag(sTag)))

    {

        CreateObject(OBJECT_TYPE_CREATURE,sTag,GetLocation(GetObjectByTag("POST_" + sTag)));

    }

}

void DonSuits()

{

    object oPC;

    int nMax = GetPartyMemberCount();

    int nIdx;

    effect eChange = EffectDisguise(DISGUISE_TYPE_ENVIRONMENTSUIT);

    for(nIdx = 0;nIdx < nMax; nIdx++)

    {

        ApplyEffectToObject(DURATION_TYPE_PERMANENT,eChange,GetPartyMemberByIndex(nIdx));

    }

}



void RemoveSuits()

{

    int nDisguize = EFFECT_TYPE_DISGUISE;//replace with effect constant

    object oPC;

    effect eEffect;

    int nMax = GetPartyMemberCount();

    int nIdx;

    for(nIdx = 0;nIdx < nMax; nIdx++)

    {

        oPC = GetPartyMemberByIndex(nIdx);

        eEffect = GetFirstEffect(oPC);

        while(GetIsEffectValid(eEffect))

        {

            if(GetEffectType(eEffect) == nDisguize)

            {

                RemoveEffect(oPC,eEffect);

            }

            eEffect = GetNextEffect(oPC);

        }

    /*  if(GetTag(oPC) == "Bastila")

        {

            ApplyEffectToObject(DURATION_TYPE_PERMANENT,EffectDisguise(4),oPC);

        }

        if(GetTag(oPC) == "Carth")

        {

            ApplyEffectToObject(DURATION_TYPE_PERMANENT,EffectDisguise(6),oPC);

        }*/

    }

}



void DeactivateTurrets(string sTag = "")

{

    if(sTag == "")

    {

        sTag = GetTag(OBJECT_SELF);

    }

    int nNth = 0;

    object oTurret = GetObjectByTag(sTag,nNth);

    while(GetIsObjectValid(oTurret))

    {

        if(oTurret != OBJECT_SELF &&

           GetObjectType(oTurret) == OBJECT_TYPE_CREATURE)

        {

            ChangeToStandardFaction(oTurret,STANDARD_FACTION_NEUTRAL);

        }

        nNth++;

        oTurret = GetObjectByTag(sTag,nNth);

    }

}



//This global indicates that Hukta threatened player

int GetHuktaThreatenedPlayerGlobal()

{

    return GetGlobalBoolean("man_HuktaThreatened");

}



void SetHuktaThreatenedPlayerGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("man_HuktaThreatened", bValue);

    }

    return;

}



//This global indicates that the player lost his last race

int GetPlayerLostLastRaceGlobal()

{

    return GetGlobalBoolean("man_PlayerLostLast");

}



void SetPlayerLostLastRaceGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("man_PlayerLostLast", bValue);

    }

    return;

}



//This global measures the state of the swoop races on Manaan

int GetManaanRaceStateGlobal()

{

    return GetGlobalNumber("man_ManaanRaceState");

}



void SetManaanRaceStateGlobal(int bValue)

{

    SetGlobalNumber("man_ManaanRaceState", bValue);



    return;

}



//This global measures the state of Queedle during the swoop races on Manaan

int GetQueedleStateGlobal()

{

    return GetGlobalNumber("tat_QueedleState");

}



void SetQueedleStateGlobal(int bValue)

{

    SetGlobalNumber("tat_QueedleState", bValue);



    return;

}



//This global indicates that player gave money to Queedle

int GetQueedleUpgradeGlobal()

{

    return GetGlobalBoolean("man_QueedleUpgrade");

}



void SetQueedleUpgradeGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("man_QueedleUpgrade", bValue);

    }

    return;

}



//This global indicates that player has angered Hukta by winning against him

int GetHuktaMadGlobal()

{

    return GetGlobalBoolean("man_HuktaMad");

}



void SetHuktaMadGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("man_HuktaMad", bValue);

    }

    return;

}



int GetPlayerNotPaidLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Race Coordinator in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetPlayerNotPaidLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Race Coordinator in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetObjectByTag("man26_swpreg"), SW_PLOT_BOOLEAN_01, bValue);

    }

}



int GetPlayerPersuadedOnceLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Race Coordinator in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetPlayerPersuadedOnceLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Race Coordinator in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }

}



int GetCasandraMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Casandra in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetCasandraMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Casandra in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }

}



int GetToldCasandraNameLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Casandra in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetToldCasandraNameLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Casandra in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }

}





int GetToldHuktaNameLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Hukta in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetToldHuktaNameLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Hukta in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }

}



int GetQueedleMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Queedle in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetQueedleMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Queedle in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }

}



int GetToldQueedleNameLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Queedle in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetToldQueedleNameLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Queedle in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }

}



int GetQueedleLeavingLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Queedle in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetQueedleLeavingLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for Queedle in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }

}



int GetQueedleToldAboutMoneyLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for Queedle in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04);

}



void SetQueedleToldAboutMoneyLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for Queedle in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04, bValue);

    }

}



int GetQueedleGaveMoneyBackLocal()

{

    // This uses SW_PLOT_BOOLEAN_05 for Queedle in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05);

}



void SetQueedleGaveMoneyBackLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_05 for Queedle in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05, bValue);

    }

}



int GetSwoopStoreInitialLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Yortal in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetSwoopStoreInitialLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Yortal in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }

}



int GetSwoopSithMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for swoop sith in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetSwoopSithMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for swoop sith in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }

}



int GetSecondSwoopSithMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for second swoop sith in the area man_26ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetSecondSwoopSithMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for second swoop sith in the area man_26ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }

}



int HasNeverTriggered()

{

    int bReturn;

    if(UT_GetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_10) == FALSE)

    {

        bReturn = TRUE;

        UT_SetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_10,TRUE);

    }

    return bReturn;

}





void SetOpponent(int nOpponent)

{

    SetGlobalNumber("MAN_SWOOP_OPP",nOpponent);

}



int GetOpponent()

{

    return GetGlobalNumber("MAN_SWOOP_OPP");

}



void SetTokenRaceTime(int nToken, int nRacerTime)

{

    // calculate the time components

    int nMinutes = nRacerTime/6000;

    int nSeconds = (nRacerTime - (nMinutes * 6000)) / 100;

    int nFractions =  nRacerTime - ((nMinutes * 6000) + (nSeconds * 100));



    //building the time string

    string sTime = IntToString(nMinutes) + ":";

    if (nSeconds < 10)

    {

        sTime = sTime + "0";

    }

    sTime = sTime + IntToString(nSeconds) + ":";

    if(nFractions < 10)

    {

        sTime = sTime + "0";

    }

    sTime = sTime + IntToString(nFractions);

    SetCustomToken(nToken,sTime);



}





void DestroyFish(object oArea)

{

    object oFish = GetFirstObjectInArea(oArea,OBJECT_TYPE_PLACEABLE);

    while (GetIsObjectValid(oFish))

    {

        string sTag = GetTag(oFish);

        string sPlaceable = GetStringLeft(sTag,10);

        if (sPlaceable == "FirixaFish")

        {

            DestroyObject(oFish);

        }

        oFish = GetNextObjectInArea(oArea,OBJECT_TYPE_PLACEABLE);

    }

  /*  object oCreature = GetFirstObjectInArea(oArea);

    while (GetIsObjectValid(oCreature))

    {

        if(GetRacialType(oCreature) == RACIAL_TYPE_HUMAN)

        {

            DestroyObject(oCreature);

        }

        oCreature =GetNextObjectInArea(oArea);

    }

    object oEnc = GetFirstObjectInArea(oArea,OBJECT_TYPE_ENCOUNTER);

    while (GetIsObjectValid(oEnc))

    {

        SetEncounterActive(FALSE,oEnc);

        oEnc = GetNextObjectInArea(oArea,OBJECT_TYPE_ENCOUNTER);

    } */

}



int GetManaanMainPlotVariable()

{

    return GetGlobalNumber("MAN_PLANET_PLOT");

}



int KoltoDestroyed()

{

    return GetGlobalNumber("MAN_PLANET_PLOT") == PLOT_KOLTO_DESTROYED;

}



void ClearSelkathFromThisLevel()

{

    string sTag = "man28_inssel";

    int nLength = GetStringLength(sTag);

    object oSelkath = GetFirstObjectInArea(OBJECT_SELF,OBJECT_TYPE_ALL);

    while(GetIsObjectValid(oSelkath))

    {

        if(GetObjectType(oSelkath) == OBJECT_TYPE_CREATURE)

        {

            if(GetStringLeft(GetTag(oSelkath),nLength) == sTag)

            {

                DelayCommand(0.1,DestroyObject(oSelkath,0.0,TRUE));

            }



        }

        if(GetObjectType(oSelkath) == OBJECT_TYPE_ENCOUNTER)

        {

            if(GetEncounterActive(oSelkath))

            {

                SetEncounterActive(FALSE,oSelkath);

            }

        }

        oSelkath = GetNextObjectInArea(OBJECT_SELF,OBJECT_TYPE_ALL);

    }

}



void OpenAssociatedDoor()

{

    string sNum = GetStringRight(GetTag(OBJECT_SELF),1);

    object oDoor = GetObjectByTag("man27_h2o0" + sNum);

    AssignCommand(oDoor,ActionOpenDoor(oDoor));

}



void CloseAssociatedDoor()

{

    string sNum = GetStringRight(GetTag(OBJECT_SELF),1);

    object oDoor = GetObjectByTag("man27_h2o0" + sNum);

    AssignCommand(oDoor,ActionCloseDoor(oDoor));

}



int GetRoomFull(string sRoom)

{



    int bFilled = FALSE;

    if(sRoom != "")

    {

        bFilled = GetGlobalBoolean("MAN_WATER_" + sRoom);

    }

    return bFilled;

}



void SetRoomFull(string sRoom, int nValue)

{

    if (GetRoomFull(sRoom) != nValue)

    {

        SetGlobalBoolean("MAN_WATER_" + sRoom,nValue);

        ActivateWaterDisplays(sRoom,nValue);

    }

}



void CloseAllWaterDoors()

{

    object oDoor = GetFirstObjectInArea(GetArea(OBJECT_SELF),OBJECT_TYPE_DOOR);

    while(GetIsObjectValid(oDoor))

    {

        if(GetStringLeft(GetTag(oDoor),9) == "man27_h2o")

        {

            AssignCommand(oDoor,ActionCloseDoor(oDoor));

        }

        oDoor = GetNextObjectInArea(GetArea(OBJECT_SELF),OBJECT_TYPE_DOOR);

    }

}



void OpenWaterDoor(string sRoom1,string sRoom2 = "")

{

    if(!GetRoomFull(sRoom1) && !GetRoomFull(sRoom2))

    {

        ActionOpenDoor(OBJECT_SELF);

    }

    else

    {

        BarkString(GetPartyMemberByIndex(0),32128);

    }

}



void SwitchWaterRooms()

{

        if (GetRoomFull("A"))

    {

        SetRoomFull("A",FALSE);

        SetRoomFull("B",TRUE);

    }

    else if(GetRoomFull("B"))

    {

        SetRoomFull("A",TRUE);

        SetRoomFull("B",FALSE);

    }

    if (GetRoomFull("C"))

    {

        SetRoomFull("C",FALSE);

        SetRoomFull("D",TRUE);

    }

    else if(GetRoomFull("D"))

    {

        SetRoomFull("C",TRUE);

        SetRoomFull("D",FALSE);

    }

    if (GetRoomFull("E"))

    {

        SetRoomFull("E",FALSE);

        SetRoomFull("F",TRUE);

    }

    else if(GetRoomFull("F"))

    {

        SetRoomFull("E",TRUE);

        SetRoomFull("F",FALSE);

    }

}



int GetIsVentActive(object oVent = OBJECT_SELF)

{

    return UT_GetPlotBooleanFlag(oVent,SW_PLOT_BOOLEAN_04);

}



void SetVentActive(int bState,object oVent = OBJECT_SELF)

{

    int nNth = 0;

    object oSteam = GetObjectByTag(STEAM_PLACEABLE + GetStringRight(GetTag(oVent),1),nNth );

    while(GetIsObjectValid(oSteam))

    {

        if(bState)

        {

            //AurPostString(GetTag(oVent) + " on",5,5 + StringToInt(GetStringRight(GetTag(oVent),1)),5.0f);

            AssignCommand(oSteam,PlayAnimation(ANIMATION_PLACEABLE_ACTIVATE));

        }

        else

        {

            AssignCommand(oSteam,PlayAnimation(ANIMATION_PLACEABLE_DEACTIVATE));

        }

        nNth++;

        oSteam = GetObjectByTag(STEAM_PLACEABLE + GetStringRight(GetTag(oVent),1),nNth );

    }

    UT_SetPlotBooleanFlag(oVent,SW_PLOT_BOOLEAN_04,bState);



}



void ActivateWaterDisplays(string sRoom,int nValue)

{

    int nNth = 0;

    object oDisplay = GetObjectByTag("man27_waterlvl" + sRoom,nNth);

    while (GetIsObjectValid(oDisplay))

    {

        if(nValue)

        {

            AssignCommand(oDisplay,ActionPlayAnimation(ANIMATION_PLACEABLE_ACTIVATE));

        }

        else

        {

            AssignCommand(oDisplay,ActionPlayAnimation(ANIMATION_PLACEABLE_DEACTIVATE));

        }

        nNth++;

        oDisplay = GetObjectByTag("man27_waterlvl" + sRoom,nNth);

    }

}



void PlayInjecterAnimation(int nLevel)

{

    int nAnim;

    object oInjector = GetObjectByTag("man28_inject");

    if(nLevel == 0)

    {

        nAnim = ANIMATION_PLACEABLE_ANIMLOOP04;

    }

    else if(nLevel == 1)

    {

        nAnim = ANIMATION_PLACEABLE_ANIMLOOP03;

    }

    else if(nLevel == 2)

    {

        nAnim = ANIMATION_PLACEABLE_ANIMLOOP02;

    }

    else if(nLevel >= 3)

    {

        nAnim = ANIMATION_PLACEABLE_ANIMLOOP01;

    }

    AssignCommand(oInjector, ActionPlayAnimation(nAnim));

}



void PlayContainerAnimation(int nLevel)

{

    int nAnim;

    object oInjector = GetObjectByTag("man28_contain");

    if(nLevel == 0)

    {

       //AurPostString("level 0",5,5,5.0);

        nAnim = ANIMATION_PLACEABLE_ANIMLOOP06;

    }

    else if(nLevel == 1)

    {

        nAnim = ANIMATION_PLACEABLE_ANIMLOOP05;

    }

    else if(nLevel == 2)

    {

        nAnim = ANIMATION_PLACEABLE_ANIMLOOP04;

    }

    else if(nLevel == 3)

    {

        nAnim = ANIMATION_PLACEABLE_ANIMLOOP03;

    }

    else if(nLevel == 4)

    {

        nAnim = ANIMATION_PLACEABLE_ANIMLOOP02;

    }

    else if(nLevel >= 3)

    {

        nAnim = ANIMATION_PLACEABLE_ANIMLOOP01;

    }

    AssignCommand(oInjector, ActionPlayAnimation(nAnim));

}



void InitiateSitters()

{

    int nNth = 0;

    object oPlaceable = GetObjectByTag("man_drinking",nNth);

    while (GetIsObjectValid(oPlaceable))

    {

        AssignCommand(oPlaceable,ActionPlayAnimation(ANIMATION_PLACEABLE_ANIMLOOP02));

        nNth++;

        oPlaceable = GetObjectByTag("man_drinking",nNth);

    }

    nNth = 0;

    oPlaceable = GetObjectByTag("man_cards",nNth);

    while (GetIsObjectValid(oPlaceable))

    {

        AssignCommand(oPlaceable,ActionPlayAnimation(ANIMATION_PLACEABLE_ANIMLOOP03));

        nNth++;

        oPlaceable = GetObjectByTag("man_cards",nNth);

    }

    nNth = 0;

    oPlaceable = GetObjectByTag("man_sitting",nNth);

    while (GetIsObjectValid(oPlaceable))

    {

        AssignCommand(oPlaceable,ActionPlayAnimation(ANIMATION_PLACEABLE_ANIMLOOP01));

        nNth++;

        oPlaceable = GetObjectByTag("man_sitting",nNth);

    }

}



int GetManaanStarMapFound()

{

    return GetGlobalBoolean("MAN_STARMAP_FOUND");

}



void TurnOffPartyAI()

{

    int nIdx;

    object oNPC;

    for(nIdx = 0; nIdx <= 2; nIdx++)

    {

       oNPC = GetPartyMemberByIndex(nIdx);

       if(GetIsObjectValid(oNPC) &&

          GetFirstPC() != oNPC)

       {

            ExecuteScript("k_pman_aioff",oNPC);



       }

    }

}



void TurnOnPartyAI()

{

    int nIdx;

    object oNPC;

    for(nIdx = 0; nIdx <= 2; nIdx++)

    {

       oNPC = GetPartyMemberByIndex(nIdx);

       if(GetIsObjectValid(oNPC) &&

          GetFirstPC() != oNPC)

       {

            ExecuteScript("k_pman_aion",oNPC);



       }

    }

}



int GetRolandIsPostPlot()

{

    object oRoland = GetObjectByTag(ROLAND_TAG);

    int nReturn;

    if(GetIsObjectValid(oRoland))

    {

        nReturn = UT_GetPlotBooleanFlag(oRoland,SW_PLOT_BOOLEAN_05);

    }

    else

    {

        nReturn = FALSE;

    }

    return nReturn;

}



void SetRolandIsPostPlot(int nValue)

{

    object oRoland = GetObjectByTag(ROLAND_TAG);

    if(GetIsObjectValid(oRoland))

    {

        UT_SetPlotBooleanFlag(oRoland,SW_PLOT_BOOLEAN_05,nValue);

    }

}



int GetMissingSelkathPlotVariable()

{

    return GetGlobalNumber("MAN_MISSING_PLOT");

}



void SetMissingSelkathPlotVariable(int nValue)

{

    SetGlobalNumber("MAN_MISSING_PLOT",nValue);

}



int GetIsSashaDead()

{

    return GetGlobalBoolean("MAN_KILLS_DONE");

}



void SetIsSashaDead()

{

    SetGlobalBoolean("MAN_KILLS_DONE",TRUE);

}

''',

    'k_inc_stunt': b'''//:: Stunt/Render Include

/*

     This Include File runs

     the stunt and cutscenes

     for the game.

*/

//:: Created By: Preston Watamaniuk

//:: Copyright (c) 2002 Bioware Corp.



//INDIVIDUAL STUNT MODULE CALLS ******************************************************************************************************



//LEV_A: Pulled out of hyperspace by the Leviathan, load STUNT_16

void ST_PlayLevCaptureStunt();

//LEV_A: Capture by the Leviathan, load ebo_m40aa

void ST_PlayLevCaptureStunt02();

//Load Turret Module Opening 07_3

void ST_PlayStuntTurret_07_3();

//Plays the Bastila torture scene

void ST_PlayBastilaTorture();

//Load Turret Module Opening 07_4

void ST_PlayStuntTurret_07_4();

//Load Leviathan Bombardment Stunt_06 covered by Render 5

void ST_PlayTarisEscape();

//Load Stunt_07 covered by Render 6a and 05_1C

void ST_PlayTarisEscape02();

//Load the Fighter Mini-Game m12ab covered by Render 07_3

void ST_PlayTarisEscape03();

//Load Dantooine module covered by hyperspace and dant landing

void ST_PlayDantooineLanding();

//Leaving Dantooine for the first time, going to STUNT_12 covered by Dant takeoff and hyperspace

void ST_PlayDantooineTakeOff();

//Plays the correct vision based on the value of K_FUTURE_PLANET from a stunt module

void ST_PlayVisionStunt();

//Plays the correct vision based on the value of K_FUTURE_PLANET with a take-off

void ST_PlayVisionStunt02();

//Plays the starforge approach

void ST_PlayStarForgeApproach();

//Plays the Damage Ebon Hawk Stunt scene

void ST_PlayStunt35();

//Shows the crash landing on the Unknown World

void ST_PlayUnknownWorldLanding();

//Shows the take-off from the Unknown World

void ST_PlayUnknownWorldTakeOff();

//Landing on the Star Forge

void ST_PlayStarForgeLanding();

//Goes to the Leviathan Mini-Game covered by the Escape Render

void ST_PlayLeviathanEscape01();



//UBER FUNCTIONS *********************************************************************************************************************



//This determines what to play after a Fighter Mini Game is run

void ST_PlayPostTurret();

//Play the appropriate take off render

string ST_GetTakeOffRender();

//Play the appropriate landing render

string ST_GetLandingRender();

//Plays the appropriate landing sequence for the chosen planet unless Lev or Star Forge

void ST_PlayGenericLanding();

//This determines what planet the PC is taking off of and plays the STUNT_14 in the appropriate manner

void ST_PlayStunt14();

//Checks if the planet designated as K_FUTURE_PLANET has had a vision played for it

int ST_VisionPlayed();

//With no cutscene between planets the game can go to a vision or straight to another planet.

void ST_PlayPlanetToPlanet();

//Play the transition from a vision to a particular planet.  This is only called at the end of a Vision STUNT_00

void ST_PlayVisionLanding();

//Fetches the correct Starmap Vision Render

string ST_GetStarmapVisionRender();

//This gets the current planet that the character is on and determines what skybox to set for the Ebon Hawk.

void ST_SetEbonHawkSkyBox();

// Fetches the correct Starmap Vision Render for the planet the player is currently on

string ST_GetCurrentStarmapVisionRender();

// Allows the Ebon Hawk to continue to the selected planet after the Leviathan unless that planet is Dantooine.

void ST_PlayPostEbo_m40ad();



void ST_MyPrintString(string sString);

void ST_MyPostString(string sString);



//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

////////////////// SINGLE STUNT/RENDER CALLS /////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



//Load Leviathan Bombardment Stunt_06 covered by Render 5

void ST_PlayTarisEscape()

{

    StartNewModule("STUNT_06", "", "05");

}

//Load Stunt_07 covered by Render 6a and 05_1C

void ST_PlayTarisEscape02()

{

    StartNewModule("STUNT_07", "", "06a", "05_1C");

}

//Load the Fighter Mini-Game m12ab covered by Render 07_3

void ST_PlayTarisEscape03()

{

    SetGlobalNumber("K_TURRET_SKYBOX", 5);

    StartNewModule("m12ab", "", "11a");

}

//Load Dantooine danm13 module covered by hyperspace and dant landing

void ST_PlayDantooineLanding()

{

    SetGlobalNumber("K_CURRENT_PLANET", 15);

    StartNewModule("danm13","","05_2A");

}



//LEV_A: Pulled out of hyperspace by the Leviathan, load STUNT_16

void ST_PlayLevCaptureStunt()

{

    string sRender = ST_GetTakeOffRender();

    SetGlobalNumber("K_CURRENT_PLANET", 40);

    StartNewModule("STUNT_16", "",  sRender, "08");

}

//LEV_A: Capture by the Leviathan, load ebo_m40aa

void ST_PlayLevCaptureStunt02()

{

    StartNewModule("ebo_m40aa","", "17");

}

//Plays the Bastila torture scene

void ST_PlayBastilaTorture()

{

    StartNewModule("STUNT_18", "", ST_GetTakeOffRender(), "08");

}

//Load Turret Module Opening 07_3

void ST_PlayStuntTurret_07_3()

{

    StartNewModule("m12ab","",  "11a");

}

//Load Turret Module Opening 07_4

void ST_PlayStuntTurret_07_4()

{

    StartNewModule("m12ab","",  "11a");

}

//Leaving Dantooine for the first time

void ST_PlayDantooineTakeOff()

{

    StartNewModule("STUNT_12","", "05_2C", "08");

}

//Plays the correct vision based on the value of K_FUTURE_PLANET

void ST_PlayVisionStunt()

{

    StartNewModule("STUNT_00","", "07_1");

}

//Plays the correct vision based on the value of K_FUTURE_PLANET with a take-off

void ST_PlayVisionStunt02()

{

    StartNewModule("STUNT_00","", ST_GetTakeOffRender(), "08");

}

//Plays the starforge approach

void ST_PlayStarForgeApproach()

{

    StartNewModule("STUNT_34", "", "33");

}

//Plays the Damage Ebon Hawk Stunt scene

void ST_PlayStunt35()

{

    StartNewModule("STUNT_35", "", "07_2");

}

//Shows the crash landing on the Unknown World

void ST_PlayUnknownWorldLanding()

{

    SetGlobalNumber("K_CURRENT_PLANET", 45);

    StartNewModule("ebo_m41aa","", "05_8A");

}

//Shows the take-off from the Unknown World

void ST_PlayUnknownWorldTakeOff()

{

    /*

        STUNT_44    05_8C   5_9 = DARK SIDE   1

        STUNT_42    05_8C   5_9 = LIGHT SIDE  2

    */

    int nChoice = GetGlobalNumber("G_FINALCHOICE");

    if(nChoice == 1)

    {

        StartNewModule("STUNT_44", "", "05_8C", "5_9");

    }

    else if(nChoice == 2)

    {

        StartNewModule("STUNT_42", "", "05_8C", "5_9");

    }

    if(nChoice == 1 || nChoice == 2)

    {

        SetGlobalNumber("K_KOTOR_MASTER", 60);

    }

}

//Landing on the Star Forge

void ST_PlayStarForgeLanding()

{

    StartNewModule("ebo_m12aa", "", "43");

    SetGlobalNumber("K_CURRENT_PLANET", 50);

}



//Goes to the Leviathan Mini-Game covered by the Escape Render

void ST_PlayLeviathanEscape01()

{

    SetGlobalNumber("K_TURRET_SKYBOX", 10);

    StartNewModule("m12ab", "", "17a", "11a");

}



//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

////////////////// GENERIC RENDER HANDLER ////////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



//::///////////////////////////////////////////////

//:: Play Post Turret Sequence

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

   This determines what to play after a Fighter

   Mini Game is run

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 14, 2002

//:://////////////////////////////////////////////

void ST_PlayPostTurret()

{

    ST_MyPrintString(" Start: ST_PlayPostTurret()");

    SetGlobalNumber("K_TURRET_SKYBOX", -1);

    int nStarMap = GetGlobalNumber("K_STAR_MAP");

    int nKOTOR = GetGlobalNumber("K_KOTOR_MASTER");

    int nSimu = GetGlobalBoolean("K_HK47_SIMULATION");

    int nRandom = GetGlobalBoolean("K_RANDOM_MINI_GAME");

    ST_MyPostString("Firing Play Post Turret " + IntToString(nSimu));



    if(nSimu == TRUE)

    {

        SetGlobalBoolean("K_HK47_SIMULATION", FALSE);

        StartNewModule("ebo_m12aa", "K_MINI_GAME");

    }

    else if(nRandom == TRUE)

    {

        SetGlobalBoolean("K_RANDOM_MINI_GAME", FALSE);

        StartNewModule("ebo_m12aa", "", "11b", ST_GetLandingRender());

        SetGlobalNumber("K_CURRENT_PLANET", GetGlobalNumber("K_FUTURE_PLANET"));

    }

    else if(nStarMap == 0 && nKOTOR == 10) //Blasting Off Taris for Dantooine

    {

        //MODIFIED by Preston Watamaniuk, March 6, 2003

        //Add this variable so I could get the space skybox to show up on the Taris To Dantooine Run

        SetGlobalBoolean("K_SPACE_SKYBOX_ON", TRUE);

        StartNewModule("ebo_m12aa", "K_TARIS_DESTROYED","11b");

    }

    else if(nStarMap == 40 && nKOTOR == 20) //Blasting Off the Leviathan

    {

        StartNewModule("ebo_m40ad", "","11b");

    }

    else if(nStarMap == 50 && nKOTOR == 40) //Landing on the Unknown World

    {

        ST_PlayStunt35();

    }

}



//::///////////////////////////////////////////////

//:: Play STUNT_14 Cutscene

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This determines what planet the PC is taking

    off of and plays the STUNT_14 in the

    appropriate manner

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 14, 2002

//:://////////////////////////////////////////////

void ST_PlayStunt14()

{

    ST_MyPrintString(" Start: ST_PlayStunt14()");



    StartNewModule("STUNT_14","",  ST_GetTakeOffRender());

}



//::///////////////////////////////////////////////

//:: Play Landing Sequence

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Plays the appropriate landing sequence for the

    chosen planet unless Lev or Star Forge

    Sets K_CURRENT_PLANET as well.   Note that

    this is played after a stunt module between

    planets.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 14, 2002

//:://////////////////////////////////////////////

void ST_PlayGenericLanding()

{

    ST_MyPrintString(" Start: ST_PlayGenericLanding()");



    if(ST_VisionPlayed() == TRUE)

    {

        StartNewModule("ebo_m12aa","",  ST_GetLandingRender());

        SetGlobalNumber("K_CURRENT_PLANET", GetGlobalNumber("K_FUTURE_PLANET"));

    }

    else

    {

        ST_PlayVisionStunt();

    }

}



//::///////////////////////////////////////////////

//:: Play Planet to Planet

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    With no cutscene between planets the game can

    go to a vision or straight to another planet.

    If interrupted by a vision then this will be

    finished by a call in ST_PlayVisionLanding

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 14, 2002

//:://////////////////////////////////////////////



void ST_PlayPlanetToPlanet()

{

    ST_MyPrintString(" Start: ST_PlayPlanetToPlanet()");

    int nRoll = d100();

    if(ST_VisionPlayed() == TRUE)

    {

        //MODIFIED by Preston Watamaniuk, March 6, 2003

        //I have put a 50% chance of being ambushed by Sith Fighters when doing a straight planet to planet transition.

        if(nRoll > 50)

        {

            ST_MyPrintString(" Start: Random Mini-Game Attack");

            //Set this so that the function ST_PlayPostTurret will know what to do.

            SetGlobalBoolean("K_RANDOM_MINI_GAME", TRUE);

            StartNewModule("m12ab", "", ST_GetTakeOffRender(), "11a");

        }

        else

        {

            StartNewModule("ebo_m12aa","",  ST_GetTakeOffRender(), "08", ST_GetLandingRender());

            SetGlobalNumber("K_CURRENT_PLANET", GetGlobalNumber("K_FUTURE_PLANET"));

        }

    }

    else

    {

        ST_PlayVisionStunt02();

    }

}



//::///////////////////////////////////////////////

//:: Play Vision Stunt and Landing

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    If the landing is broken by a STUNT_00 then

    the landing will be finished with this function.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 14, 2002

//:://////////////////////////////////////////////



void ST_PlayVisionLanding()

{

    ST_MyPrintString(" Start: ST_PlayVisionLanding()");

    int nFUTURE = GetGlobalNumber("K_FUTURE_PLANET");

    if(nFUTURE == 20 ||

       nFUTURE == 25 ||

       nFUTURE == 30 ||

       nFUTURE == 35)

    {

        StartNewModule("ebo_m12aa","", ST_GetStarmapVisionRender(), ST_GetLandingRender());

        SetGlobalNumber("K_CURRENT_PLANET", GetGlobalNumber("K_FUTURE_PLANET"));

    }

}



//::///////////////////////////////////////////////

//:: Play Post ebo_m40ad

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Allows the Ebon Hawk to continue to the

    selected planet after the Leviathan unless

    that planet is Dantooine.

    0    Endar Spire     5

    1    Taris           10

    2    Dantooine       15

    3    --Kashyyk       20

    4    --Manaan        25

    5    --Korriban      30

    6    --Tatooine      35

    7    Leviathan       40

    8    Unknown World   45

    9    Star Forge      50

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: March 21, 2003

//:://////////////////////////////////////////////

void ST_PlayPostEbo_m40ad()

{

    ST_MyPrintString(" Start: ST_PlayGenericLanding()");

    int nFPlanet = GetGlobalNumber("K_FUTURE_PLANET");



    if(nFPlanet == 15)

    {

        if(GetGlobalBoolean("K_STAR_MAP_KASHYYYK") == FALSE)

        {

            nFPlanet = 20;

        }

        else if(GetGlobalBoolean("K_STAR_MAP_MANAAN") == FALSE)

        {

            nFPlanet = 25;

        }

        else if(GetGlobalBoolean("K_STAR_MAP_KORRIBAN") == FALSE)

        {

            nFPlanet = 30;

        }

        else if(GetGlobalBoolean("K_STAR_MAP_TATOOINE") == FALSE)

        {

            nFPlanet = 35;

        }

    }

    SetGlobalNumber("K_FUTURE_PLANET", nFPlanet);

    if(ST_VisionPlayed() == TRUE)

    {

        StartNewModule("ebo_m12aa","",  ST_GetLandingRender());

        SetGlobalNumber("K_CURRENT_PLANET", nFPlanet);

    }

    else

    {

        ST_PlayVisionStunt();

    }

}



//::///////////////////////////////////////////////

//:: Get Take-Off Render

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns the appropriate take off render based

    on the K_CURRENT_PLANET variable

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 14, 2002

//:://////////////////////////////////////////////



string ST_GetTakeOffRender()

{

    int nCURRENT = GetGlobalNumber("K_CURRENT_PLANET");

    if(nCURRENT == 15)

    {

        return "05_2c";

    }

    else if(nCURRENT == 20)

    {

        return "05_4c";

    }

    else if(nCURRENT == 25)

    {

        return "05_5c";

    }

    else if(nCURRENT == 30)

    {

        return "05_7C";

    }

    else if(nCURRENT == 35)

    {

        return "05_3c";

    }

    else if(nCURRENT == 40)

    {

        return  "NULL";

    }

    else if(nCURRENT == 45)

    {

        return "05_8c";

    }

    else if(nCURRENT == 55)

    {

        return "LIVE_1c";

    }

    else if(nCURRENT == 60)

    {

        return "LIVE_2c";

    }

    else if(nCURRENT == 65)

    {

        return "LIVE_3c";

    }

    else if(nCURRENT == 70)

    {

        return "LIVE_4c";

    }

    else if(nCURRENT == 75)

    {

        return "LIVE_5c";

    }

    else if(nCURRENT == 80)

    {

        return "LIVE_6c";

    }

    return "NULL";

}



//::///////////////////////////////////////////////

//:: Get Landing Render

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns the appropriate landing render based

    on the K_FUTURE_PLANET variable

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 14, 2002

//:://////////////////////////////////////////////

string ST_GetLandingRender()

{

    int nFUTURE = GetGlobalNumber("K_FUTURE_PLANET");

    if(nFUTURE == 15)

    {

        return "05_2a";

    }

    else if(nFUTURE == 20)

    {

        return "05_4a";

    }

    else if(nFUTURE == 25)

    {

        return "05_5a";

    }

    else if(nFUTURE == 30)

    {

        return "05_7a";

    }

    else if(nFUTURE == 35)

    {

        return "05_3a";

    }

    else if(nFUTURE == 40)

    {

        return  "NULL";

    }

    else if(nFUTURE == 55)

    {

        return "LIVE_1a";

    }

    else if(nFUTURE == 60)

    {

        return "LIVE_2a";

    }

    else if(nFUTURE == 65)

    {

        return "LIVE_3a";

    }

    else if(nFUTURE == 70)

    {

        return "LIVE_4a";

    }

    else if(nFUTURE == 75)

    {

        return "LIVE_5a";

    }

    else if(nFUTURE == 80)

    {

        return "LIVE_6a";

    }

    return  "NULL";

}



//::///////////////////////////////////////////////

//:: Has Vision Played

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks if the planet designated as

    K_FUTURE_PLANET has had a vision played for it

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watmanaiuk

//:: Created On: Dec 14, 2002

//:://////////////////////////////////////////////

int ST_VisionPlayed()

{

    int nVision = GetGlobalNumber("Ebon_Vision");

    int nFUTURE = GetGlobalNumber("K_FUTURE_PLANET");



    ST_MyPrintString(" Start: ST_VisionPlayed()");

    ST_MyPrintString(" nFuture = " + IntToString(nFUTURE));

    ST_MyPrintString("k_vis_kashyyyk2  = " + IntToString(GetGlobalBoolean("k_vis_kashyyyk2")));

    ST_MyPrintString("k_vis_manaan2  = " + IntToString(GetGlobalBoolean("k_vis_manaan2")));

    ST_MyPrintString("k_vis_korriban2  = " + IntToString(GetGlobalBoolean("k_vis_korriban2")));

    ST_MyPrintString("k_vis_tatooine2  = " + IntToString(GetGlobalBoolean("k_vis_tatooine2")));



    if(nFUTURE == 20 && GetGlobalBoolean("k_vis_kashyyyk2") == FALSE)

    {

        SetGlobalBoolean("k_vis_kashyyyk2", TRUE);

        return FALSE;

    }

    else if(nFUTURE == 25 && GetGlobalBoolean("k_vis_manaan2") == FALSE)

    {

        SetGlobalBoolean("k_vis_manaan2", TRUE);

        return FALSE;

    }

    else if(nFUTURE == 30 && GetGlobalBoolean("k_vis_korriban2") == FALSE)

    {

        SetGlobalBoolean("k_vis_korriban2", TRUE);

        return FALSE;

    }

    else if(nFUTURE == 35 && GetGlobalBoolean("k_vis_tatooine2") == FALSE)

    {

        SetGlobalBoolean("k_vis_tatooine2", TRUE);

        return FALSE;

    }



    ST_MyPrintString("Returning True");

    return TRUE;

}



//::///////////////////////////////////////////////

//:: Fetch Starmap Render

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Fetches the correct Starmap Vision Render

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Dec 14, 2002

//:://////////////////////////////////////////////



string ST_GetStarmapVisionRender()

{

    int nFUTURE = GetGlobalNumber("K_FUTURE_PLANET");



    if(nFUTURE == 20)

    {

        return "0C";

    }

    else if(nFUTURE == 25)

    {

        return "0B";

    }

    else if(nFUTURE == 30)

    {

        return "0D";

    }

    else if(nFUTURE == 35)

    {

        return "0A";

    }

    return "NULL";

}



//::///////////////////////////////////////////////

//:: Set Ebon Hawk Skybox

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This gets the current planet that the character

    is on and determines what skybox to set for

    the Ebon Hawk.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: March 6, 2003

//:://////////////////////////////////////////////

void ST_SetEbonHawkSkyBox()

{

    int nFUTURE = GetGlobalNumber("K_CURRENT_PLANET");



    if(GetGlobalBoolean("K_SPACE_SKYBOX_ON") == TRUE)

    {

        ST_MyPrintString("Firing Anim 09 for Space");

        ST_MyPrintString("New Print Line Confirmation");

        PlayRoomAnimation("m12aa_01q", ANIMATION_ROOM_SCRIPTLOOP09);

        SetGlobalBoolean("K_SPACE_SKYBOX_ON", FALSE);

    }

    else if(nFUTURE == 15)

    {

        ST_MyPrintString("Firing Anim 02 for Dantooine");

        PlayRoomAnimation("m12aa_01q", ANIMATION_ROOM_SCRIPTLOOP02);

    }

    else if(nFUTURE == 20)

    {

        ST_MyPrintString("Firing Anim 01 for Kashyyyk");

        PlayRoomAnimation("m12aa_01q", ANIMATION_ROOM_SCRIPTLOOP01);

    }

    else if(nFUTURE == 25)

    {

        ST_MyPrintString("Firing Anim 06 for Manaan");

        PlayRoomAnimation("m12aa_01q", ANIMATION_ROOM_SCRIPTLOOP06);

    }

    else if(nFUTURE == 30)

    {

        ST_MyPrintString("Firing Anim 05 for Korriban");

        PlayRoomAnimation("m12aa_01q", ANIMATION_ROOM_SCRIPTLOOP05);

    }

    else if(nFUTURE == 35)

    {

        ST_MyPrintString("Firing Anim 04 for Tatooine");

        PlayRoomAnimation("m12aa_01q", ANIMATION_ROOM_SCRIPTLOOP04);

    }

    else if(nFUTURE == 40)

    {

        ST_MyPrintString("Firing Anim 08 for Leviathan");

        PlayRoomAnimation("m12aa_01q", ANIMATION_ROOM_SCRIPTLOOP08);

    }

    else if(nFUTURE == 45)

    {

        ST_MyPrintString("Firing Anim 07 for Unknown World");

        PlayRoomAnimation("m12aa_01q", ANIMATION_ROOM_SCRIPTLOOP07);

    }

    else if(nFUTURE == 50)

    {

        ST_MyPrintString("Firing Anim 03 for Star Forge");

        PlayRoomAnimation("m12aa_01q", ANIMATION_ROOM_SCRIPTLOOP03);

    }

    //MODIFIED by Preston Watamaniuk on May 10, 2003

    //Skybox added for live planets.

    else if(nFUTURE > 50)

    {

        ST_MyPrintString("Firing Anim 10 for all live content planets");

        PlayRoomAnimation("m12aa_01q", ANIMATION_ROOM_SCRIPTLOOP10);

    }

    else

    {

        PlayRoomAnimation("m12aa_01q", ANIMATION_ROOM_SCRIPTLOOP09);

    }

}



void ST_MyPrintString(string sString)

{

    PrintString("RENDER/STUNT Debug ****************** " + sString);

}



void ST_MyPostString(string sString)

{

    AurPostString("RENDER/STUNT Debug ****************** " + sString, 10, 10, 4.0);

}



//::///////////////////////////////////////////////

//:: Fetch Starmap Render

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Fetches the correct Starmap Vision Render

    for the planet the player is currently on

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: March 13, 2003

//:://////////////////////////////////////////////



string ST_GetCurrentStarmapVisionRender()

{

    int nFUTURE = GetGlobalNumber("K_CURRENT_PLANET");



    if(nFUTURE == 20)

    {

        return "0C";

    }

    else if(nFUTURE == 25)

    {

        return "0B";

    }

    else if(nFUTURE == 30)

    {

        return "0D";

    }

    else if(nFUTURE == 35)

    {

        return "0A";

    }

    return "NULL";

}



''',

    'k_inc_switch': b'''//:: k_inc_switch

/*

     A simple include defining all of the

     events in the game as constants.

*/

//:: Created By: Preston Watamaniuk

//:: Copyright (c) 2002 Bioware Corp.



//DEFAULT AI EVENTS

int KOTOR_DEFAULT_EVENT_ON_HEARTBEAT           = 1001;

int KOTOR_DEFAULT_EVENT_ON_PERCEPTION          = 1002;

int KOTOR_DEFAULT_EVENT_ON_COMBAT_ROUND_END    = 1003;

int KOTOR_DEFAULT_EVENT_ON_DIALOGUE            = 1004;

int KOTOR_DEFAULT_EVENT_ON_ATTACKED            = 1005;

int KOTOR_DEFAULT_EVENT_ON_DAMAGE              = 1006;

int KOTOR_DEFAULT_EVENT_ON_DEATH               = 1007;

int KOTOR_DEFAULT_EVENT_ON_DISTURBED           = 1008;

int KOTOR_DEFAULT_EVENT_ON_BLOCKED             = 1009;

int KOTOR_DEFAULT_EVENT_ON_FORCE_AFFECTED      = 1010;

int KOTOR_DEFAULT_EVENT_ON_GLOBAL_DIALOGUE_END = 1011;

int KOTOR_DEFAULT_EVENT_ON_PATH_BLOCKED        = 1012;



//HENCHMEN AI EVENTS

int KOTOR_HENCH_EVENT_ON_HEARTBEAT           = 2001;

int KOTOR_HENCH_EVENT_ON_PERCEPTION          = 2002;

int KOTOR_HENCH_EVENT_ON_COMBAT_ROUND_END    = 2003;

int KOTOR_HENCH_EVENT_ON_DIALOGUE            = 2004;

int KOTOR_HENCH_EVENT_ON_ATTACKED            = 2005;

int KOTOR_HENCH_EVENT_ON_DAMAGE              = 2006;

int KOTOR_HENCH_EVENT_ON_DEATH               = 2007;

int KOTOR_HENCH_EVENT_ON_DISTURBED           = 2008;

int KOTOR_HENCH_EVENT_ON_BLOCKED             = 2009;

int KOTOR_HENCH_EVENT_ON_FORCE_AFFECTED      = 2010;

int KOTOR_HENCH_EVENT_ON_GLOBAL_DIALOGUE_END = 2011;

int KOTOR_HENCH_EVENT_ON_PATH_BLOCKED        = 2012;

int KOTOR_HENCH_EVENT_ON_ENTER_5m            = 2013;

int KOTOR_HENCH_EVENT_ON_EXIT_5m             = 2014;



//MISC AI EVENTS

int KOTOR_MISC_DETERMINE_COMBAT_ROUND                = 3001;

int KOTOR_MISC_DETERMINE_COMBAT_ROUND_ON_PC          = 3002;

int KOTOR_MISC_DETERMINE_COMBAT_ROUND_ON_INDEX_ZERO  = 3003;



''',

    'k_inc_tar': b'''//::///////////////////////////////////////////////

//:: k_inc_tar

//:: k_inc_tar

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

  include file for taris

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 16, 2002

//:://////////////////////////////////////////////

#include "k_inc_debug"

#include "k_inc_utility"



//performs a standard creature transformation where the original creature

//is destroyed and a new creature is put in its place.  returns a reference

//to the new creature.

object TAR_TransformCreature(object oTarget = OBJECT_INVALID,string sTemplate = "");



//test routine for walking waypoints

void TAR_WalkWaypoints();



//mark an object for cleanup by the TAR_CleanupDeadObjects function

void TAR_MarkForCleanup(object obj = OBJECT_SELF);



//destroy all objects whose PLOT_10 flag has been set

void TAR_CleanupDeadObjects(object oArea);



//make object do an uninterruptible path move

void TAR_PlotMovePath(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE);



//make object do an uninterruptible move to an object

void TAR_PlotMoveObject(object oTarget,int nRun = FALSE);



//make object do an uninterruptible move to a location

void TAR_PlotMoveLocation(location lTarget,int nRun = FALSE);



//check for rukil's apprentice journal

int TAR_PCHasApprenticeJournal();



//return number of promised land journals player has

int TAR_GetNumberPromisedLandJournals();



//toggle the state of sith armor

void TAR_ToggleSithArmor();



//fill container with treasure from table

void TAR_AddTreasureToContainer(object oContainer,int iTable,int iAmount);



//returns TRUE if object is wearing sith armor

int TAR_GetWearingSithArmor(object oTarget = OBJECT_INVALID);



//strip sith armor from party, equipping another appropriate item (if available)

//returns the sith armor object if it was being worn

object TAR_StripSithArmor();



//teleport party member

void TAR_TeleportPartyMember(object oPartyMember, location lDest);



//makes the sith armor equippable

void TAR_EnableSithArmor();



//strip all items from an object

void TAR_StripCharacter(object oTarget,object oDest);



//::///////////////////////////////////////////////

//:: TAR_TransformCreature

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//performs a standard creature transformation where the original creature

//is destroyed and a new creature is put in its place.  returns a reference

//to the new creature.

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 16, 2002

//:://////////////////////////////////////////////

object TAR_TransformCreature(object oTarget = OBJECT_INVALID,string sTemplate = "")

{

  if(GetIsObjectValid(oTarget) && sTemplate != "")

  {

    location lPlace = GetLocation(oTarget);



    DestroyObject(oTarget,0.0,TRUE);

    return(CreateObject(OBJECT_TYPE_CREATURE,sTemplate,lPlace));

  }

  else

  {

    return(OBJECT_INVALID);

  }

}



//::///////////////////////////////////////////////

//:: TAR_WalkWaypoints

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//test routine for walking waypoints

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 29, 2002

//:://////////////////////////////////////////////

void TAR_WalkWaypoints()

{

  object oNextWP = OBJECT_INVALID;

  string sWPPath = "";



  if(UT_GetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_01))

  {

    sWPPath = "ptar_testwp1";

  }

  else if(UT_GetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_02))

  {

    sWPPath = "ptar_testwp2";

  }

  else if(UT_GetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_03))

  {

    sWPPath = "ptar_testwp3";

  }

  else if(UT_GetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_04))

  {

    sWPPath = "ptar_testwp4";

  }

  else if(UT_GetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_05))

  {

    sWPPath = "ptar_testwp5";

  }

  else

  {

    sWPPath = "ptar_testwp6";

  }

  

  if(UT_GetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_06))

  {

    sWPPath = sWPPath + "_1";

    UT_SetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_06,FALSE);

  }

  else

  {

    sWPPath = sWPPath + "_0";

    UT_SetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_06,TRUE);

  }

  

  oNextWP = GetObjectByTag(sWPPath);

  

  Db_PostString("MOVING TO " + GetTag(oNextWP),5,5,2.0);

  //ClearAllActions();

  ActionForceMoveToObject(oNextWP);

  ActionDoCommand(TAR_WalkWaypoints());

}



//::///////////////////////////////////////////////

//:: TAR_MarkForCleanup

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//mark an object for cleanup by the TAR_CleanupDeadObjects function

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 16, 2002

//:://////////////////////////////////////////////

void TAR_MarkForCleanup(object obj = OBJECT_SELF)

{

  UT_SetPlotBooleanFlag(obj,SW_PLOT_BOOLEAN_10,TRUE);

}



//::///////////////////////////////////////////////

//:: TAR_CleanupDeadObjects

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//destroy all objects whose PLOT_10 flag has been set

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 15, 2002

//:://////////////////////////////////////////////

void TAR_CleanupDeadObjects(object oArea)

{

  object obj;



  obj = GetFirstObjectInArea(oArea);

  //Db_PostString("START CLEANUP...",5,7,5.0);

  while(GetIsObjectValid(obj))

  {

    //Db_PostString("FOUND OBJ",5,6,5.0);

    if(UT_GetPlotBooleanFlag(obj,SW_PLOT_BOOLEAN_10))

    {

      //Db_PostString("CLEANING UP OBJECT",5,5,5.0);

      DestroyObject(obj,0.0,TRUE);

    }

    obj = GetNextObjectInArea(oArea);

  }

}



//::///////////////////////////////////////////////

//:: TAR_PlotMovePath

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//make object do an uninterruptible path move

//based on code done by Aidan (actually, pretty much a copy)

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 16, 2002

//:://////////////////////////////////////////////

void TAR_PlotMovePath(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE)

{



    int nInc = 1;

    object oWP;

    int nIdx;

    if(nFirst > nLast)

    {

        nInc = -1;

    }

    for(nIdx = nFirst - nInc; abs(nLast - nIdx) > 0 && abs(nLast - nIdx) <= abs((nLast - nFirst) + 1); nIdx = nIdx + nInc)

    {

        oWP = GetObjectByTag(sWayPointTag + IntToString(nIdx + nInc));

        if(GetIsObjectValid(oWP))

        {

            ActionForceMoveToObject(oWP,nRun);

        }

    }

    ActionDoCommand(SetCommandable(TRUE));

    SetCommandable(FALSE);

}



//::///////////////////////////////////////////////

//:: TAR_PlotMoveObject

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//make object do an uninterruptible move to an object

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 16, 2002

//:://////////////////////////////////////////////

void TAR_PlotMoveObject(object oTarget,int nRun = FALSE)

{

  ActionForceMoveToObject(oTarget,nRun);

  ActionDoCommand(SetCommandable(TRUE));

  SetCommandable(FALSE);

}



//::///////////////////////////////////////////////

//:: TAR_PlotMoveObject

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//make object do an uninterruptible move to a location

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 16, 2002

//:://////////////////////////////////////////////

void TAR_PlotMoveLocation(location lTarget,int nRun = FALSE)

{

  ActionForceMoveToLocation(lTarget,nRun);

  ActionDoCommand(SetCommandable(TRUE));

  SetCommandable(FALSE);

}



//::///////////////////////////////////////////////

//:: TAR_PCHasApprenticeJournal

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//check for rukil's apprentice journal

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 21, 2002

//:://////////////////////////////////////////////

int TAR_PCHasApprenticeJournal()

{

  return(GetIsObjectValid(GetItemPossessedBy(GetFirstPC(),"ptar_appjournal")));

}



//::///////////////////////////////////////////////

//:: TAR_GetNumberPromisedLandJournals

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//return number of promised land journals player has

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 21, 2002

//:://////////////////////////////////////////////

int TAR_GetNumberPromisedLandJournals()

{

  object oInv;

  int iJournals = 0;

  

  oInv = GetFirstItemInInventory(GetFirstPC());

  while(GetIsObjectValid(oInv))

  {

    if(GetTag(oInv) == "ptar_rukjournal")

    {

      Db_PostString("JOURNALS - " + IntToString(GetNumStackedItems(oInv)),5,5,5.0);

      iJournals += GetNumStackedItems(oInv);

    }

    oInv = GetNextItemInInventory(GetFirstPC());

  }

  

  return(iJournals);

}



//::///////////////////////////////////////////////

//:: TAR_ToggleSithArmor

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//toggle the state of sith armor

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: Oct. 8, 2002

//:://////////////////////////////////////////////

void TAR_ToggleSithArmor()

{

  int i;

  object obj;

  

  obj = GetItemActivated();

  if(GetTag(obj) != "ptar_sitharmor")

  {

    return;

  }

  

  i = 1;

  obj = GetNearestCreature(CREATURE_TYPE_RACIAL_TYPE,RACIAL_TYPE_ALL,GetFirstPC(),i);

  while(GetIsObjectValid(obj))

  {

    if(GetDistanceBetween(obj,GetFirstPC()) < 10.0 && !IsObjectPartyMember(obj))

    {

      ActionStartConversation(GetFirstPC(),"ptar_armor_dlg");

      return;

    }

    i++;

    obj = GetNearestCreature(CREATURE_TYPE_RACIAL_TYPE,RACIAL_TYPE_ALL,GetFirstPC(),i);

  }

  

  ActionStartConversation(GetFirstPC(),"ptar_armon_dlg");

  SetGlobalBoolean("TAR_SITHARMOR",!GetGlobalBoolean("TAR_SITHARMOR"));

}



//fill container with treasure from table

void TAR_AddTreasureToContainer(object oContainer,int iTable,int iAmount)

{

  int i;

  

  if(!GetIsObjectValid(oContainer))

  {

    return;

  }

  

  for(i = 0;i < iAmount;i++)

  {

    switch(iTable)

    {

    case 0:

      switch(Random(3))

      {

      case 0:

        CreateItemOnObject("G_I_CREDITS001",oContainer,Random(20) + 1);

        break;

      case 1:

        CreateItemOnObject("G_I_DRDREPEQP001",oContainer);

        break;

      case 2:

        CreateItemOnObject("G_I_MEDEQPMNT04",oContainer);

        break;

      default:

        CreateItemOnObject("G_I_MEDEQPMNT01",oContainer);

      }

      break;

    case 1:

      switch(Random(11))

      {

      case 0:

        CreateItemOnObject("G_W_BLSTRPSTL001",oContainer);

        break;

      case 1:

        CreateItemOnObject("G_I_SECSPIKE01",oContainer);

        break;

      case 2:

        CreateItemOnObject("G_I_PROGSPIKE01",oContainer);

        break;

      case 3:

        CreateItemOnObject("G_A_CLASS5001",oContainer);

        break;

      case 4:

        CreateItemOnObject("G_W_FRAGGREN01",oContainer);

        break;

      case 5:

        CreateItemOnObject("G_W_STUNGREN01",oContainer);

        break;

      case 6:

        CreateItemOnObject("G_W_IONGREN01",oContainer);

        break;

      case 7:

        CreateItemOnObject("G_W_SONICGREN01",oContainer);

        break;

      case 8:

        CreateItemOnObject("G_W_VBROSHORT01",oContainer);

        break;

      case 9:

        CreateItemOnObject("G_W_STUNBATON01",oContainer);

        break;

      default:

        CreateItemOnObject("G_I_CREDITS001",oContainer,Random(40) + 20);

        break;

      }

      break;

    case 2:

      switch(Random(5))

      {

      case 0:

        CreateItemOnObject("G_W_BLSTRPSTL001",oContainer);

        break;

      case 1:

        CreateItemOnObject("G_W_QTRSTAFF01",oContainer);

        break;

      case 2:

        CreateItemOnObject("G_I_MEDEQPMNT01",oContainer);

        break;

      case 3:

        CreateItemOnObject("G_A_CLASS4001",oContainer);

        break;

      default:

        CreateItemOnObject("G_I_CREDITS001",oContainer,Random(20) + 1);

        break;

      }

      break;

    }

  }

}





int TAR_GetWearingSithArmor(object oTarget = OBJECT_INVALID)

{

  int i;

  object obj;

  object oArmorItem = GetItemInSlot(INVENTORY_SLOT_BODY,oTarget);



  if(!GetIsObjectValid(oTarget))

  {

    for(i = 0;i < GetPartyMemberCount();i++)

    {

      obj = GetPartyMemberByIndex(i);

      oArmorItem = GetItemInSlot(INVENTORY_SLOT_BODY,obj);

      if(GetTag(oArmorItem) == "ptar_sitharmor")

      {

        return(TRUE);

      }

    }

    return(FALSE);

  }

  return(GetTag(oArmorItem) == "ptar_sitharmor");

}



//strip sith armor from target, equipping another appropriate item (if available)

object TAR_StripSithArmor()

{

  object oArmor = OBJECT_INVALID;

  object obj;

  object oTarget;

  int i;



  Db_PostString("STRIPPING ARMOR = " + GetTag(oTarget),5,7,5.0);



  for(i = 0;i < GetPartyMemberCount();i++)

  {

    oTarget = GetPartyMemberByIndex(i);

    

    if(TAR_GetWearingSithArmor(oTarget))

    {

      Db_PostString("ARMOR STRIPPED",5,8,5.0);

      oArmor = GetItemInSlot(INVENTORY_SLOT_BODY,oTarget);

      SetCommandable(TRUE,oTarget);

      AssignCommand(oTarget,ActionUnequipItem(oArmor));

      obj = GetFirstItemInInventory(oTarget);

      while(GetIsObjectValid(obj))

      {

        if(GetBaseItemType(obj) == BASE_ITEM_BASIC_CLOTHING)

        {

          Db_PostString("PUT ON NEW ITEM",5,9,5.0);

          AssignCommand(oTarget,ActionEquipItem(obj,INVENTORY_SLOT_BODY,TRUE));

          break;

        }

        obj = GetNextItemInInventory(oTarget);

      }

    }

    else if(GetIsObjectValid(obj = GetItemPossessedBy(oTarget,"ptar_sitharmor")))

    {

      oArmor = obj;

      Db_PostString("ARMOR FOUND",5,9,5.0);

    }

  }

  return(oArmor);

}



//teleport party member

void TAR_TeleportPartyMember(object oPartyMember, location lDest)

{

  if(!GetIsObjectValid(oPartyMember))

  {

    return;

  }

  

  SetCommandable(TRUE,oPartyMember);

  AssignCommand(oPartyMember,ClearAllActions());

  AssignCommand(oPartyMember,ActionJumpToLocation(lDest));

}



//makes the sith armor equippable

void TAR_EnableSithArmor()

{

  int i;

  object obj;

  object oArmor;

  

  for(i = 0;i < GetPartyMemberCount();i++)

  {

    obj = GetPartyMemberByIndex(i);

    if(GetIsObjectValid(oArmor = GetItemPossessedBy(obj,"ptar_sitharmor")))

    {

      SetItemNonEquippable(oArmor,FALSE);

    }

  }

}



void TAR_StripCharacter(object oTarget,object oDest)

{

  object oItem;



  if(!GetIsObjectValid(oTarget) || !GetIsObjectValid(oDest))

  {

    return;

  }



  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_BELT,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_BODY,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_HANDS,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_HEAD,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_IMPLANT,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_LEFTARM,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_LEFTWEAPON,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_RIGHTARM,oTarget)))

  {

    GiveItem(oItem,oDest);

  }

  if(GetIsObjectValid(oItem = GetItemInSlot(INVENTORY_SLOT_RIGHTWEAPON,oTarget)))

  {

    GiveItem(oItem,oDest);

  }



  oItem = GetFirstItemInInventory(oTarget);

  while(GetIsObjectValid(oItem))

  {

    GiveItem(oItem,oDest);

    oItem = GetFirstItemInInventory(oTarget);

  }

}





''',

    'k_inc_tat': b'''//::///////////////////////////////////////////////

//:: Include

//:: k_inc_tat

//:: Copyright (c) 2002 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This is the include file for Tatooine.

*/

//:://////////////////////////////////////////////

//:: Created By: John Winski

//:: Created On: September 3, 2002

//:://////////////////////////////////////////////

#include "k_inc_utility"

#include "k_inc_generic"

// racer constants

int NONE = 0;

int GARM = 1;

int YUKA = 2;

int ZORIIS = 3;



// race time constants

int GARM_TIME = 2600;

int YUKA_TIME = 2470;

int ZORIIS_TIME = 2350;

string RACE_DEFAULT = GetStringByStrRef(32289);



int GetGammoreansDeadGlobal()

{

    return GetGlobalBoolean("tat_GammoreansDead");

}



void SetGammoreansDeadGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_GammoreansDead", bValue);

    }

    return;

}



int GetMetKomadLodgeGlobal()

{

    return GetGlobalBoolean("tat_MetKomadLodge");

}



void SetMetKomadLodgeGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_MetKomadLodge", bValue);

    }

    return;

}



int GetSharinaAccusedGurkeGlobal()

{

    return GetGlobalBoolean("tat_SharinaAccused");

}



void SetSharinaAccusedGurkeGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_SharinaAccused", bValue);

    }

    return;

}



int GetKraytDeadGlobal()

{

    return GetGlobalBoolean("tat_KraytDead");

}



void SetKraytDeadGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_KraytDead", bValue);

    }

    return;

}



int GetKraytFightGlobal()

{

    return GetGlobalBoolean("tat_KraytFight");

}



void SetKraytFightGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_KraytFight", bValue);

    }

    return;

}



int GetTalkedToConserveGlobal()

{

    return GetGlobalBoolean("tat_talkconserve");

}



void SetTalkedToConserveGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_talkconserve", bValue);

    }

    return;

}



int GetUsedChokeOnCzerkaGlobal()

{

    return GetGlobalBoolean("tat_chokedczerka");

}



void SetUsedChokeOnCzerkaGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_chokedczerka", bValue);

    }

    return;

}



int GetTatooineRacerGlobal()

{

    return GetGlobalBoolean("tat_SwoopRacer");

}



void SetTatooineRacerGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_SwoopRacer", bValue);

    }



    return;

}



int GetLostLastRaceGlobal()

{

    return GetGlobalBoolean("tat_LostLastRace");

}



void SetLostLastRaceGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_LostLastRace", bValue);

    }



    return;

}



int GetTanisDeadGlobal()

{

    return GetGlobalBoolean("tat_TanisDead");

}



void SetTanisDeadGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_TanisDead", bValue);

    }



    return;

}



int GetPlayerDestroyedOneGlobal()

{

    return GetGlobalBoolean("tat_OneDroidDead");

}



void SetPlayerDestroyedOneGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_OneDroidDead", bValue);

    }



    return;

}



int GetTanisGiveUpGlobal()

{

    return GetGlobalBoolean("tat_TanisGiveUp");

}



void SetTanisGiveUpGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_TanisGiveUp", bValue);

    }



    return;

}



int GetAskAboutHuntGlobal()

{

    return GetGlobalBoolean("tat_AskAboutHunt");

}



void SetAskAboutHuntGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_AskAboutHunt", bValue);

    }



    return;

}



int GetGammoreanWarningGlobal()

{

    return GetGlobalBoolean("tat_TrustGammNot");

}



void SetGammoreanWarningGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_TrustGammNot", bValue);

    }



    return;

}



int GetGammoreanGoneGlobal()

{

    return GetGlobalBoolean("tat_GammGone");

}



void SetGammoreanGoneGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_GammGone", bValue);

    }



    return;

}



int GetGammoreanBribeGlobal()

{

    return GetGlobalBoolean("tat_GammBribe");

}



void SetGammoreanBribeGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_GammBribe", bValue);

    }



    return;

}



int GetRaceCompleteGlobal()

{

    return GetGlobalNumber("tat_RaceComplete");

}



void SetRaceCompleteGlobal(int bValue)

{

    SetGlobalNumber("tat_RaceComplete", bValue);



    return;

}



int GetSandHistoryStateGlobal()

{

    return GetGlobalNumber("tat_SandHistory");

}



void SetSandHistoryStateGlobal(int bValue)

{

    SetGlobalNumber("tat_SandHistory", bValue);



    return;

}



int GetToldHowToBeWarriorGlobal()

{

    return GetGlobalNumber("tat_SandWarrior");

}



void SetToldHowToBeWarriorGlobal(int bValue)

{

    SetGlobalNumber("tat_SandWarrior", bValue);



    return;

}



int GetRaceWonNotPaidGlobal()

{

    return GetGlobalBoolean("tat_NotPaid");

}



void SetRaceWonNotPaidGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_NotPaid", bValue);

    }



    return;

}



int GetSharinaPaidFullGlobal()

{

    return GetGlobalBoolean("tat_SharinaPaidFull");

}



void SetSharinaPaidFullGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_SharinaPaidFull", bValue);

    }



    return;

}



int GetTalkTanisGlobal()

{

    return GetGlobalBoolean("tat_TalkTanis");

}



void SetTalkTanisGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_TalkTanis", bValue);

    }



    return;

}



int GetMadTanisGlobal()

{

    return GetGlobalBoolean("tat_MadTanis");

}



void SetMadTanisGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_MadTanis", bValue);

    }



    return;

}



int GetTanisSavedGlobal()

{

    return GetGlobalBoolean("tat_TanisSaved");

}



void SetTanisSavedGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_TanisSaved", bValue);

    }



    return;

}



int GetTuskenJobGlobal()

{

    return GetGlobalBoolean("tat_TuskenJob");

}



void SetTuskenJobGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_TuskenJob", bValue);

    }



    return;

}



int GetJawaCaptiveGlobal()

{

    return GetGlobalNumber("tat_JawaCaptive");

}



void SetJawaCaptiveGlobal(int bValue)

{

    SetGlobalNumber("tat_JawaCaptive", bValue);



    return;

}



int GetIzizCaptiveGlobal()

{

    return GetGlobalNumber("tat_IzizCaptive");

}



void SetIzizCaptiveGlobal(int bValue)

{

    SetGlobalNumber("tat_IzizCaptive", bValue);



    return;

}



int GetIzizGotMadGlobal()

{

    return GetGlobalNumber("tat_IzizGotMad");

}



void SetIzizGotMadGlobal(int bValue)

{

    SetGlobalNumber("tat_IzizGotMad", bValue);



    return;

}



int GetGriffCaptiveGlobal()

{

    return GetGlobalNumber("tat_GriffCaptive");

}



void SetGriffCaptiveGlobal(int bValue)

{

    SetGlobalNumber("tat_GriffCaptive", bValue);



    return;

}



int GetMissionCaptiveGlobal()

{

    return GetGlobalNumber("tat_MissCaptive");

}



void SetMissionCaptiveGlobal(int bValue)

{

    SetGlobalNumber("tat_MissCaptive", bValue);



    return;

}



int GetFazzaPazzakStateGlobal()

{

    return GetGlobalNumber("tat_fazzpazzstate");

}



void SetFazzaPazzakStateGlobal(int bValue)

{

    SetGlobalNumber("tat_fazzpazzstate", bValue);



    return;

}



int GetGriffGreetaGlobal()

{

    return GetGlobalBoolean("tat_GriffGreeta");

}



void SetGriffGreetaGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_GriffGreeta", bValue);

    }

    return;

}



int GetGriffPortGlobal()

{

    return GetGlobalBoolean("tat_GriffPort");

}



void SetGriffPortGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_GriffPort", bValue);

    }

    return;

}



int GetDockingPaidLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the Czerka official in area kas_m17ab.



    return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01);

}



void SetDockingPaidLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the Czerka official in area kas_m17ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetPlayerWarnedAboutQuestionsLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Sand People Storyteller in area tat_20aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetPlayerWarnedAboutQuestionsLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Sand People Storyteller in area tat_20aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetHK47CriticisedOnceLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Sand People Storyteller in area tat_20aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetHK47CriticisedOnceLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Sand People Storyteller in area tat_20aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetDorakNamedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Dorak Quinn in area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetDorakNamedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the Dorak Quinn in area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetGurkePissedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m17ad.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01);

}



void SetGurkePissedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetGurkeNamedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Gurke in area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetGurkeNamedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Gurke in area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetJunixTatooineInfoLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Junix Nard in area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetJunixTatooineInfoLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Junix nard in area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetJunixSaidSwoopLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Junix nard in area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetJunixSaidSwoopLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Junix nard in area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetJunixSaidKorribanLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Junix nard in area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetJunixSaidKorribanLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for Junix nard in area tat_m17afd.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetJunixSaidKoltoLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for Junix nard in area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04);

}



void SetJunixSaidKoltoLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for Junix nard in area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetJunixSaidWookieeLocal()

{

    // This uses SW_PLOT_BOOLEAN_05 for Junix nard in area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05);

}



void SetJunixSaidWookieeLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_05 for Junix nard in area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetCelisNicoInfoLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m17ae.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01);

}



void SetCelisNicoInfoLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m17ae.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetBulliedNicoLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for the area tat_m17ae.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_02);

}



void SetBulliedNicoLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for the area tat_m17ae.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetCelisDealLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for the area tat_m17ae.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_03);

}



void SetCelisDealLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for the area tat_m17ae.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetNicoHappyLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Nico in the area tat_m17ae.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetNicoHappyLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Nico in the area kas_m17ae.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetNicoTalkTimesSubstituteLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Nico in the area tat_m17ae.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetNicoTalkTimesSubstituteLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Nico in the area tat_m17ae.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetMottaPaidThePlayerLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Motta in the area tat_m17ae.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetMottaPaidThePlayerLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Motta in the area tat_m17ae.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetGarmNamedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Garm Totryl in the area tat_m17ae.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetGarmNamedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Garm Totryl in the area tat_m17ae.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetYukarNamedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Yuka Rill in the area tat_m17ae.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetYukarNamedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Yuka Rill in the area tat_m17ae.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetYukarMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Yuka Rill in the area tat_m17ae.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetYukarMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Yuka Rill in the area tat_m17ae.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetZoriisNamedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Zoriis Bafka in the area tat_m17ae.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetZoriisNamedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Zoriis Bafka in the area tat_m17ae.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetHK47InfoLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Yuka Laka in the area tat_m17ac.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetHK47InfoLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Yuka Laka in the area tat_m17ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetHK47SoldLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for Yuka Laka in the area tat_m17ac.



    return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_02);

}



void SetHK47SoldLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for Yuka Laka in the area tat_m17ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetYukalPersuadeLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Yuka Laka in the area tat_m17ac.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetYukalPersuadeLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for Yuka Laka in the area tat_m17ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetYukaHKFourThousandLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for Yuka Laka in the area tat_m17ac.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04);

}



void SetYukaHKFourThousandLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for Yuka Laka in the area tat_m17ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetYukaHKThreeThousandLocal()

{

    // This uses SW_PLOT_BOOLEAN_05 for Yuka Laka in the area tat_m17ac.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05);

}



void SetYukaHKThreeThousandLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_05 for Yuka Laka in the area tat_m17ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetYukaHKTwentyFiveHundredLocal()

{

    // This uses SW_PLOT_BOOLEAN_06 for Yuka Laka in the area tat_m17ac.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_06);

}



void SetYukaHKTwentyFiveHundredLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_06 for Yuka Laka in the area tat_m17ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_06, bValue);

    }



    return;

}



int GetYukaThreatenedOverPriceLocal()

{

    // This uses SW_PLOT_BOOLEAN_07 for Yuka Laka in the area tat_m17ac.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_07);

}



void SetYukaThreatenedOverPriceLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_07 for Yuka Laka in the area tat_m17ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_07, bValue);

    }



    return;

}



int GetYukaSaidSwoopChampionLocal()

{

    // This uses SW_PLOT_BOOLEAN_08 for Yuka Laka in the area tat_m17ac.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_08);

}



void SetYukaSaidSwoopChampionLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_08 for Yuka Laka in the area tat_m17ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_08, bValue);

    }



    return;

}



int GetYukaSaidKoltoGoneLocal()

{

    // This uses SW_PLOT_BOOLEAN_09 for Yuka Laka in the area tat_m17ac.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_09);

}



void SetYukaSaidKoltoGoneLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_09 for Yuka Laka in the area tat_m17ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_09, bValue);

    }



    return;

}



int GetYukaSaidWookieesRevoltedGlobal()

// set when yuka talks about wookies

{

    return GetGlobalBoolean("tat_YukaWookiees");

}



void SetYukaSaidWookieesRevoltedGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_YukaWookiees", bValue);

    }

    return;

}



int GetYukaSaidPowerStruggleGlobal()

// set when yuka talks about power struggle

{

    return GetGlobalBoolean("tat_YukaStruggle");

}



void SetYukaSaidPowerStruggleGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_YukaStruggle", bValue);

    }

    return;

}



int GetPlayerRacedAtAllGlobal()

// set when yuka talks about power struggle

{

    return GetGlobalBoolean("tat_playerhasraced");

}



void SetPlayerRacedAtAllGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_playerhasraced", bValue);

    }

    return;

}



int GetGandroffMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Gandroff in the area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetGandroffMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Gandroff in the area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetGandroffNameLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Gandroff in the area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetGandroffNameLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Gandroff in the area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetGandrofForceNoTalkLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Gandroff in the area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetGandrofForceNoTalkLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for Gandroff in the area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetPazzakLastGameLostLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Pazzak on Furko Nellis in the area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetPazzakLastGameLostLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Pazzak on Furko Nellis in the area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetPazzakGame1WonLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Pazzak on Furko Nellis in the area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetPazzakGame1WonLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Pazzak on Furko Nellis in the area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetPazzakGame2WonLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Pazzak on Furko Nellis in the area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetPazzakGame2WonLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for Pazzak on Furko Nellis in the area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetPazzakGame3WonLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for Pazzak on Furko Nellis in the area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04);

}



void SetPazzakGame3WonLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for Pazzak on Furko Nellis in the area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetPazzakJustPlayedLocal()

{

    // This uses SW_PLOT_BOOLEAN_05 for Pazzak on Furko Nellis in the area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05);

}



void SetPazzakJustPlayedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_05 for Pazzak on Furko Nellis in the area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetFazzaPazzakPlayedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Pazzak on alien player in the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetFazzaPazzakPlayedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Pazzak on alien player in the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetFazzaLostLastGameLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Pazzak on alien player in the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetFazzaLostLastGameLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Pazzak on alien player in the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetToldOfFazzaPazzakLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Pazzak on alien player in the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetToldOfFazzaPazzakLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for Pazzak on alien player in the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetKomadNameLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for komad in the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetKomadNameLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Komad in the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetKomadMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for komad in the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetKomadMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Komad in the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetTanisNameLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Tanis in the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetTanisNameLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Tanis in the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetQuestionTanisAboutWifeLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Tanis in the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetQuestionTanisAboutWifeLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Tanis in the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetTanisIgnoredLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Tanis in the area tat_m18aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetTanisIgnoredLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Tanis in the area tat_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetGammoreanAmbushLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the ambush droid in the area tat_m18aa.



    return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01);

}



void SetGammoreanAmbushLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the ambush droid in the area tat_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetAskedTanisForPaymentLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Tanis in the area tat_m18aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetAskedTanisForPaymentLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Tanis in the area tat_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetAskedTanisForCreditsLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Tanis in the area tat_m18aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetAskedTanisForCreditsLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for Tanis in the area tat_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetAskedTanisToGiveUpLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for Tanis in the area tat_m18aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04);

}



void SetAskedTanisToGiveUpLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for Tanis in the area tat_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetTanisShoutLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_05 for Tanis in the area tat_m18aa.



    return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_05);

}



void SetTanisShoutLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_05 for Tanis in the area tat_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetDroidExplodeLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_06 for Tanis in the area tat_m18aa.



    return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_06);

}



void SetDroidExplodeLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_06 for Tanis in the area tat_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_06, bValue);

    }



    return;

}



int GetTanisCallLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_07 for Tanis in the area tat_m18aa.



    return UT_GetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_07);

}



void SetTanisCallLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_07 for Tanis in the area tat_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(oTarget, SW_PLOT_BOOLEAN_07, bValue);

    }



    return;

}



int GetOfficeMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Czerka officer in the area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetOfficeMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Czerka officer in the area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetOfficeNamedLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Czerka officer in the area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetOfficeNamedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Czerka officer in the area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetVaporatorPriceDroppedLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for greeta holda in the area tat_m17ag.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetVaporatorPriceDroppedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for greeta holda in the area tat_m17ag.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetVaporatorGivenLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for greeta holda in the area tat_m17ag.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetVaporatorGivenLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for greeta holda in the area tat_m17ag.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetGreetaSaidSwoopLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for greeta holda in the area tat_m17ag.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04);

}



void SetGreetaSaidSwoopLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for greeta holda in the area tat_m17ag.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetGreetaSaidKorribanLocal()

{

    // This uses SW_PLOT_BOOLEAN_05 for greeta holda in the area tat_m17ag.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05);

}



void SetGreetaSaidKorribanLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_05 for greeta holda in the area tat_m17ag.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetGreetaSaidKoltoLocal()

{

    // This uses SW_PLOT_BOOLEAN_06 for greeta holda in the area tat_m17ag.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_06);

}



void SetGreetaSaidKoltoLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_06 for greeta holda in the area tat_m17ag.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_06, bValue);

    }



    return;

}



int GetToldOfBountyLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Czerka protocol officer in the area tat_m17ag.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetToldOfBountyLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Czerka protocol officer in the area tat_m17ag.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetChieftainStickGivenLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Czerka protocol officer in the area tat_m17ag.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetChieftainStickGivenLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for Czerka protocol officer in the area tat_m17ag.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetAskedIzizStarMapLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for iziz in the area tat_m17aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetAskedIzizStarMapLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for iziz in the area tat_m17aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetIzizMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for iziz in the area tat_m17aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetIzizMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for iziz in the area tat_m17aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetIzizRewardedLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for iziz in the area tat_m17aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetIzizRewardedLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for iziz in the area tat_m17aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetIzizPaidMoreLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for iziz in the area tat_m17aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04);

}



void SetIzizPaidMoreLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for iziz in the area tat_m17aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetMechMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for mechanic in the area tat_m17aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetMechMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for mechanic in the area tat_m17aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetForcedMechanicLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for mechanic in the area tat_m17aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetForcedMechanicLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for mechanic in the area tat_m17aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetForcedNoTalkLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for mechanic in the area tat_m17aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetForcedNoTalkLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for mechanic in the area tat_m17aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetGateGuardMadLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the gate guard in the area tat_m17aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetGateGuardMadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the gate guard in the area tat_m17aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetPlayerSaidNoHuntLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Komad in the area tat_m18ac.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetPlayerSaidNoHuntLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Komad in the area tat_m18ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetPlayerSaidYesHuntLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Komad in the area tat_m18ac.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetPlayerSaidYesHuntLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Komad in the area tat_m18ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetTwoSaidSwoopLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for twohead in the area tat_m17ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetTwoSaidSwoopLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for twohead in the area tat_m17ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetTwoSaidKorribanLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for twohead in the area tat_m17ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetTwoSaidKorribanLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for twohead in the area tat_m17ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetTwoSaidKoltoLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for twohead in the area tat_m17ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetTwoSaidKoltoLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for twohead in the area tat_m17ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetTwoSaidWookieeLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for two head in the area tat_m17ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04);

}



void SetTwoSaidWookieeLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for two head in the area tat_m17ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetTwoAskedAboutSelfLocal()

{

    // This uses SW_PLOT_BOOLEAN_05 for two head in the area tat_m17ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05);

}



void SetTwoAskedAboutSelfLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_05 for two head in the area tat_m17ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetTwoAskedAboutTatooineLocal()

{

    // This uses SW_PLOT_BOOLEAN_06 for two head in the area tat_m17ab.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_06);

}



void SetTwoAskedAboutTatooineLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_06 for two head in the area tat_m17ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_06, bValue);

    }



    return;

}



int GetFazzaSaidSwoopLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for Fazza in the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02);

}



void SetFazzaSaidSwoopLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for Fazza in the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetFazzaSaidKorribanLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Fazza in the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03);

}



void SetFazzaSaidKorribanLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for Fazza in the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetFazzaSaidKoltoLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for Fazza in the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04);

}



void SetFazzaSaidKoltoLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for Fazza in the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetFazzaSaidWookieeLocal()

{

    // This uses SW_PLOT_BOOLEAN_05 for Fazza in the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05);

}



void SetFazzaSaidWookieeLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_05 for Fazza in the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetTalkedToKomadLocal()

{

    // This uses SW_PLOT_BOOLEAN_03 for Komad in the area tat_m18ac.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_03);

}



void SetTalkedToKomadLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for Komad in the area tat_m18ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetDragonSpawnLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m18ac.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01);

}



void SetDragonSpawnLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m18ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetDragonPearlLocal()

{

    // This uses SW_PLOT_BOOLEAN_02 for the area tat_m18ac.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_02);

}



void SetDragonPearlLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_02 for the area tat_m18ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}



int GetTuskenAmbush2Local()

{

    // This uses SW_PLOT_BOOLEAN_03 for the area tat_m18ac.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_03);

}



void SetTuskenAmbush2Local(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_03 for the area tat_m18ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_03, bValue);

    }



    return;

}



int GetHelenaSpawnLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m17af.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetHelenaSpawnLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m17af.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}





int GetTuskenAmbushLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the area kas_m18aa.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01);

}



void SetTuskenAmbushLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area kas_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetBanthaFollowLocal()

{

    // This uses SW_PLOT_BOOLEAN_04 for the area tat_m18ac.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_04);

}



void SetBanthaFollowLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_04 for the area tat_m18ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_04, bValue);

    }



    return;

}



int GetBanthaLuredLocal()

{

    // This uses SW_PLOT_BOOLEAN_05 for the area tat_m18ac.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_05);

}



void SetBanthaLuredLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_05 for the area tat_m18ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetKomadReadyLocal()

{

    // This uses SW_PLOT_BOOLEAN_06 for the area tat_m18ac.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_06);

}



void SetKomadReadyLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_06 for the area tat_m18ac.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_06, bValue);

    }



    return;

}



int GetFailedFixLocal()

{

    // This uses SW_PLOT_BOOLEAN_05 for the area kas_m18aa.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_05);

}



void SetFailedFixLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_05 for the area kas_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_05, bValue);

    }



    return;

}



int GetDroid1RiddleLocal()

{

    // This uses SW_PLOT_BOOLEAN_06 for the area kas_m18aa.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_06);

}



void SetDroid1RiddleLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_06 for the area kas_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_06, bValue);

    }



    return;

}



int GetDroid2RiddleLocal()

{

    // This uses SW_PLOT_BOOLEAN_07 for the area kas_m18aa.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_07);

}



void SetDroid2RiddleLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_07 for the area kas_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_07, bValue);

    }



    return;

}



int GetDroid3RiddleLocal()

{

    // This uses SW_PLOT_BOOLEAN_08 for the area kas_m18aa.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_08);

}



void SetDroid3RiddleLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_08 for the area kas_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_08, bValue);

    }



    return;

}



int GetDroid4RiddleLocal()

{

    // This uses SW_PLOT_BOOLEAN_09 for the area kas_m18aa.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_09);

}



void SetDroid4RiddleLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_09 for the area kas_m18aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_09, bValue);

    }



    return;

}



int GetSharinaWaitLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the area kas_m17aa.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01);

}



void SetSharinaWaitLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area kas_m17aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetGriffSpawnLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m20aa and tat_m17ag.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetGriffSpawnLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m20aa and tat_m17ag.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetGriffSawMissionLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for Griff in the area kas_m20aa.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetGriffSawMissionLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for Griff in the area kas_m20aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



// sets the current opponent variable

void SetOpponent(int nOpponent)

{

    SetGlobalNumber("TAT_SWOOP_OPP",nOpponent);

}



// retuens the current opponent variable

int GetOpponent()

{

    return GetGlobalNumber("TAT_SWOOP_OPP");

}



// sets the dialouge tokens based on an integer and creates it in the format

// mm:ss:ff

void SetTokenRaceTime(int nToken, int nRacerTime)

{

    // calculate the time components

    int nMinutes = nRacerTime/6000;

    int nSeconds = (nRacerTime - (nMinutes * 6000)) / 100;

    int nFractions =  nRacerTime - ((nMinutes * 6000) + (nSeconds * 100));



    //building the time string

    string sTime = IntToString(nMinutes) + ":";

    if (nSeconds < 10)

    {

        sTime = sTime + "0";

    }

    sTime = sTime + IntToString(nSeconds) + ":";

    if(nFractions < 10)

    {

        sTime = sTime + "0";

    }

    sTime = sTime + IntToString(nFractions);

    SetCustomToken(nToken,sTime);



}



// Checks if SW_PLOT_BOOLEAN_10 has been set. if not returns true and sets the boolean

int HasNeverTriggered()

{

    int bReturn;

    if(UT_GetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_10) == FALSE)

    {

        bReturn = TRUE;

        UT_SetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_10,TRUE);

    }

    return bReturn;

}



// Checks if SW_PLOT_BOOLEAN_09 has been set. if not returns true and sets the boolean

int FirstRace()

{

    int bReturn;

    if(UT_GetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_09) == FALSE)

    {

        bReturn = TRUE;

        UT_SetPlotBooleanFlag(OBJECT_SELF,SW_PLOT_BOOLEAN_09,TRUE);

    }

    return bReturn;

}



int GetKomadHuntEndGlobal()

{

    return GetGlobalBoolean("tat_KomadHuntEnd");

}



void SetKomadHuntEndGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_KomadHuntEnd", bValue);

    }



    return;

}



int GetPlayerAttemptedOfficialRaceGlobal()

{

    return GetGlobalBoolean("tat_oneofficialrace");

}



void SetPlayerAttemptedOfficialRaceGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_oneofficialrace", bValue);

    }



    return;

}



int GetPlayerGotFreeRaceGlobal()

{

    return GetGlobalBoolean("tat_freeracegiven");

}



void SetPlayerGotFreeRaceGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_freeracegiven", bValue);

    }



    return;

}



int GetKraytMapGlobal()

{

    return GetGlobalBoolean("tat_KraytMap");

}



void SetKraytMapGlobal(int bValue)

{

    if (bValue == TRUE || bValue == FALSE)

    {

        SetGlobalBoolean("tat_KraytMap", bValue);

    }



    return;

}



int GetKomadHuntingLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m17ad.



    return UT_GetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01);

}



void SetKomadHuntingLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m17ad.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(OBJECT_SELF, SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



int GetTuskenDoneLocal()

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m18ab.



    return UT_GetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01);

}



void SetTuskenDoneLocal(int bValue)

{

    // This uses SW_PLOT_BOOLEAN_01 for the area tat_m18ab.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(OBJECT_SELF), SW_PLOT_BOOLEAN_01, bValue);

    }



    return;

}



void EquipBasicClothing(object oTarget)

{

    int bFound = FALSE;



    object oParty1 = GetPartyMemberByIndex(0);

    object oParty2 = GetPartyMemberByIndex(1);

    object oParty3 = GetPartyMemberByIndex(2);

    object oItem = GetFirstItemInInventory(oTarget);



    //Issue 1  Make sure the same clothing is not equipped.

    //Issue 2  Make sure that they already have clothing.

    //Issue 3  If they do not have clothing then spawn and equip.

    //Issue 4  If they are wearing basic clothing ignore them.



    /*

    while(GetIsObjectValid(oItem) == TRUE && bFound == FALSE)

    {

        if (//GetBaseItemType(oItem) == BASE_ITEM_JEDI_ROBE &&

           (//GetLevelByClass(CLASS_TYPE_JEDICONSULAR, oTarget) > 0 ||

            //GetLevelByClass(CLASS_TYPE_JEDIGUARDIAN, oTarget) > 0 ||

            //GetLevelByClass(CLASS_TYPE_JEDISENTINEL, oTarget) > 0) &&

            GetItemInSlot(INVENTORY_SLOT_BODY, oParty1) != oItem &&

            GetItemInSlot(INVENTORY_SLOT_BODY, oParty2) != oItem &&

            GetItemInSlot(INVENTORY_SLOT_BODY, oParty3) != oItem)

        {

            AssignCommand(oTarget, ActionEquipItem(oItem, INVENTORY_SLOT_BODY,TRUE));

            bFound = TRUE;

        }

        oItem = GetNextItemInInventory(oTarget);

    }

    */



    oItem = GetFirstItemInInventory(oTarget);



    while(GetIsObjectValid(oItem) == TRUE && bFound == FALSE)

    {

        if (GetBaseItemType(oItem) == BASE_ITEM_BASIC_CLOTHING &&

            GetItemInSlot(INVENTORY_SLOT_BODY, oParty1) != oItem &&

            GetItemInSlot(INVENTORY_SLOT_BODY, oParty2) != oItem &&

            GetItemInSlot(INVENTORY_SLOT_BODY, oParty3) != oItem)

        {

            AssignCommand(oTarget, ActionEquipItem(oItem, INVENTORY_SLOT_BODY, TRUE));

            bFound = TRUE;

        }

        oItem = GetNextItemInInventory(oTarget);

    }



    if (bFound == FALSE)

    {

        oItem = CreateItemOnObject("G_A_CLOTHES01", oTarget);

        AssignCommand(oTarget, ActionEquipItem(oItem, INVENTORY_SLOT_BODY,TRUE));

    }

}





void RemoveSandpeopleDisguise()

{

    object oPC = GetFirstPC();

    object oParty1 = GetPartyMemberByIndex(0);

    object oParty2 = GetPartyMemberByIndex(1);

    object oParty3 = GetPartyMemberByIndex(2);



    object oArmor = GetItemInSlot(INVENTORY_SLOT_BODY, oParty1);



    if (GetTag(oArmor) == "tat17_sandperdis")

    {

        AssignCommand(oParty1, ClearAllActions());

        AssignCommand(oParty1, ActionUnequipItem(oArmor));

        AssignCommand(oParty1, ActionDoCommand(SetItemNonEquippable(oArmor, TRUE)));

        EquipBasicClothing(oParty1);

    }

    oArmor = GetItemInSlot(INVENTORY_SLOT_BODY, oParty2);

    if (GetTag(oArmor) == "tat17_sandperdis")

    {

        AssignCommand(oParty2, ClearAllActions());

        AssignCommand(oParty2, ActionUnequipItem(oArmor));

        AssignCommand(oParty2, ActionDoCommand(SetItemNonEquippable(oArmor, TRUE)));

        EquipBasicClothing(oParty2);

    }

    oArmor = GetItemInSlot(INVENTORY_SLOT_BODY, oParty3);

    if (GetTag(oArmor) == "tat17_sandperdis")

    {

        AssignCommand(oParty3, ClearAllActions());

        AssignCommand(oParty3, ActionUnequipItem(oArmor));

        AssignCommand(oParty3, ActionDoCommand(SetItemNonEquippable(oArmor, TRUE)));

        EquipBasicClothing(oParty3);

    }



    ActionWait(1.0);



    object oItem = GetFirstItemInInventory(oPC);



    while (GetIsObjectValid(oItem) == TRUE)

    {

        if (GetTag(oItem) == "tat17_sandperdis")

        {

            SetItemNonEquippable(oItem, TRUE);

        }



        oItem = GetNextItemInInventory(oPC);

    }

}



void DestroySandpeopleDisguise()

{

    object oPC = GetFirstPC();

    object oParty1 = GetPartyMemberByIndex(0);

    object oParty2 = GetPartyMemberByIndex(1);

    object oParty3 = GetPartyMemberByIndex(2);



    object oArmor = GetItemInSlot(INVENTORY_SLOT_BODY, oParty1);



    if (GetTag(oArmor) == "tat17_sandperdis")

    {

        AssignCommand(oParty1, ClearAllActions());

        AssignCommand(oParty1, ActionUnequipItem(oArmor));

        DestroyObject(oArmor);

        //EquipBasicClothing(oParty1);

    }

    oArmor = GetItemInSlot(INVENTORY_SLOT_BODY, oParty2);

    if (GetTag(oArmor) == "tat17_sandperdis")

    {

        AssignCommand(oParty2, ClearAllActions());

        AssignCommand(oParty2, ActionUnequipItem(oArmor));

        DestroyObject(oArmor);

        //EquipBasicClothing(oParty2);

    }

    oArmor = GetItemInSlot(INVENTORY_SLOT_BODY, oParty3);

    if (GetTag(oArmor) == "tat17_sandperdis")

    {

        AssignCommand(oParty3, ClearAllActions());

        AssignCommand(oParty3, ActionUnequipItem(oArmor));

        DestroyObject(oArmor);

        //EquipBasicClothing(oParty3);

    }



    ActionWait(1.0);



    object oItem = GetFirstItemInInventory(oPC);



    while (GetIsObjectValid(oItem) == TRUE)

    {

        if (GetTag(oItem) == "tat17_sandperdis")

        {

            DestroyObject(oItem);

        }



        oItem = GetNextItemInInventory(oPC);

    }

}



void SandpeopleDisguiseUsable()

{

    object oPC = GetFirstPC();



    object oItem = GetFirstItemInInventory(oPC);



    while (GetIsObjectValid(oItem) == TRUE)

    {

        if (GetTag(oItem) == "tat17_sandperdis")

        {

            SetItemNonEquippable(oItem, FALSE);

        }



        oItem = GetNextItemInInventory(oPC);

    }

}



int GetTuskenContainerLocal(object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for the the area tat_m20aa.



    return UT_GetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_02);

}



void SetTuskenContainerLocal(int bValue, object oTarget = OBJECT_SELF)

{

    // This uses SW_PLOT_BOOLEAN_02 for the the area tat_m20aa.



    if (bValue == TRUE || bValue == FALSE)

    {

        UT_SetPlotBooleanFlag(GetArea(oTarget), SW_PLOT_BOOLEAN_02, bValue);

    }



    return;

}

''',

    'k_inc_treasure': b'''//:: k_inc_treasure

/*

     contains code for filling containers using treasure tables

*/

//:: Created By:  Jason Booth

//:: Copyright (c) 2002 Bioware Corp.

//

//  March 15, 2003  J.B.

//      removed parts and spikes from tables

//



//constants for container types

int SWTR_DEBUG = TRUE;  //set to false to disable console/file logging

int SWTR_TABLE_CIVILIAN_CONTAINER = 1;

int SWTR_TABLE_MILITARY_CONTAINER_LOW = 2;

int SWTR_TABLE_MILITARY_CONTAINER_MID = 3;

int SWTR_TABLE_MILITARY_CONTAINER_HIGH = 4;

int SWTR_TABLE_CORPSE_CONTAINER_LOW = 5;

int SWTR_TABLE_CORPSE_CONTAINER_MID = 6;

int SWTR_TABLE_CORPSE_CONTAINER_HIGH = 7;

int SWTR_TABLE_SHADOWLANDS_CONTAINER_LOW = 8;

int SWTR_TABLE_SHADOWLANDS_CONTAINER_MID = 9;

int SWTR_TABLE_SHADOWLANDS_CONTAINER_HIGH = 10;

int SWTR_TABLE_DROID_CONTAINER_LOW = 11;

int SWTR_TABLE_DROID_CONTAINER_MID = 12;

int SWTR_TABLE_DROID_CONTAINER_HIGH = 13;

int SWTR_TABLE_RAKATAN_CONTAINER = 14;

int SWTR_TABLE_SANDPERSON_CONTAINER = 15;



//Fill an object with treasure from the specified table

//This is the only function that should be used outside this include file

void SWTR_PopulateTreasure(object oContainer,int iTable,int iItems = 1,int bUnique = TRUE);



//for internal debugging use only, output string to the log file and console if desired

void SWTR_Debug_PostString(string sStr,int bConsole = TRUE,int x = 5,int y = 5,float fTime = 5.0)

{

  if(SWTR_DEBUG)

  {

    if(bConsole)

    {

      AurPostString("SWTR_DEBUG - " + sStr,x,y,fTime);

    }

    PrintString("SWTR_DEBUG - " + sStr);

  }

}



//return whether i>=iLow and i<=iHigh

int SWTR_InRange(int i,int iLow,int iHigh)

{

  if(i >= iLow && i <= iHigh)

  {

    return(TRUE);

  }

  else

  {

    return(FALSE);

  }

}



//returns whether sTemplate is not in sFilter

int SWTR_IsUnique(string sTemplate,string sFilter)

{

  if(sFilter == "")

  {

    return(TRUE);

  }

  

  if(FindSubString(sFilter,sTemplate) >= 0)

  {

    return(FALSE);

  }

  else

  {

    return(TRUE);

  }

}



//turn a given quantity into appropriate format for a treasure blob (string)

string SWTR_GetQuantity(int iCount)

{

  string str = IntToString(iCount);

  string pad = "0";

  int length = 4;

  

  while(GetStringLength(str) < length)

  {

    str = pad + str;

  }

  return("[" + str + "]");

}



//get a single treasure blob (string) from specified table

//use sFilter to maintain uniqueness

string SWTR_GetTreasure(int iTable,string sFilter = "")

{

  int iRoll;

  string sTemplate;

  int bFound = FALSE;

  string sObjDesc = "";

  string sQuantity;

  

  //first, generate a random number (0-99) and then, using the specified table

  //lookup the treasure

  do {

    iRoll = Random(100);

    switch(iTable)

    {

    case 1:  //civilian container

      sTemplate = "G_I_CREDITS001";

      if(SWTR_InRange(iRoll,0,84) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(20)+1);

        bFound = TRUE;

      }

      /*

      sTemplate = "G_A_CLOTHES01";

      if(SWTR_InRange(iRoll,25,34) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_A_CLOTHES02";

      if(SWTR_InRange(iRoll,35,44) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_A_CLOTHES03";

      if(SWTR_InRange(iRoll,45,54) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_A_CLOTHES04";

      if(SWTR_InRange(iRoll,55,64) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_A_CLOTHES05";

      if(SWTR_InRange(iRoll,65,74) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_A_CLOTHES06";

      if(SWTR_InRange(iRoll,75,84) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "g_i_progspike01";

      if(SWTR_InRange(iRoll,85,89) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,90,94) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      */

      sTemplate = "g_i_medeqpmnt01";

      if(SWTR_InRange(iRoll,85,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 2:  //low level military container

      sTemplate = "G_I_CREDITS001";

      if(SWTR_InRange(iRoll,0,9) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(20)+1);

        bFound = TRUE;

      }

      sTemplate = "g_w_fraggren01";

      if(SWTR_InRange(iRoll,10,29) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_w_StunGren01";

      if(SWTR_InRange(iRoll,30,39) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_w_SonicGren01";

      if(SWTR_InRange(iRoll,40,59) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "g_w_iongren01";

      if(SWTR_InRange(iRoll,60,69) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      /*

      sTemplate = "g_i_progspike01";

      if(SWTR_InRange(iRoll,50,59) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,60,69) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      */

      sTemplate = "g_i_medeqpmnt01";

      if(SWTR_InRange(iRoll,70,84) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_MEDEQPMNT04";

      if(SWTR_InRange(iRoll,85,89) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_DRDREPEQP001";

      if(SWTR_InRange(iRoll,90,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 3:  //mid level military container

      sTemplate = "G_I_CREDITS001";

      if(SWTR_InRange(iRoll,0,3) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(30)+10);

        bFound = TRUE;

      }

      sTemplate = "g_w_fraggren01";

      if(SWTR_InRange(iRoll,4,17) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      sTemplate = "G_w_StunGren01";

      if(SWTR_InRange(iRoll,18,21) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      sTemplate = "G_w_SonicGren01";

      if(SWTR_InRange(iRoll,22,27) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      sTemplate = "g_w_iongren01";

      if(SWTR_InRange(iRoll,28,33) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      /*

      sTemplate = "g_i_progspike01";

      if(SWTR_InRange(iRoll,20,23) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,24,33) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      */

      sTemplate = "G_I_MEDEQPMNT02";

      if(SWTR_InRange(iRoll,34,48) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_MEDEQPMNT04";

      if(SWTR_InRange(iRoll,49,53) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      sTemplate = "G_I_DRDREPEQP002";

      if(SWTR_InRange(iRoll,54,63) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE001";

      if(SWTR_InRange(iRoll,64,75) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE002";

      if(SWTR_InRange(iRoll,76,87) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE003";

      if(SWTR_InRange(iRoll,88,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 4:  //high level military container

      sTemplate = "G_I_CREDITS001";

      if(SWTR_InRange(iRoll,0,3) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(60)+ 40);

        bFound = TRUE;

      }

      sTemplate = "g_w_fraggren01";

      if(SWTR_InRange(iRoll,4,17) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      sTemplate = "G_w_StunGren01";

      if(SWTR_InRange(iRoll,18,21) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      sTemplate = "G_w_SonicGren01";

      if(SWTR_InRange(iRoll,22,27) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      sTemplate = "g_w_iongren01";

      if(SWTR_InRange(iRoll,28,33) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      /*

      sTemplate = "g_i_progspike01";

      if(SWTR_InRange(iRoll,20,23) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,24,33) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      */

      sTemplate = "G_I_MEDEQPMNT03";

      if(SWTR_InRange(iRoll,34,48) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_MEDEQPMNT04";

      if(SWTR_InRange(iRoll,49,53) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      sTemplate = "G_I_DRDREPEQP003";

      if(SWTR_InRange(iRoll,54,63) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE004";

      if(SWTR_InRange(iRoll,64,75) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE005";

      if(SWTR_InRange(iRoll,76,87) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE006";

      if(SWTR_InRange(iRoll,88,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 5:  //low level corpse container

      sTemplate = "G_I_CREDITS001";

      if(SWTR_InRange(iRoll,0,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(20)+ 1);

        bFound = TRUE;

      }

      /*

      sTemplate = "g_i_progspike01";

      if(SWTR_InRange(iRoll,70,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,80,89) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      */

      sTemplate = "g_i_medeqpmnt01";

      if(SWTR_InRange(iRoll,80,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 6:  //mid level corpse container

      sTemplate = "G_I_CREDITS001";

      if(SWTR_InRange(iRoll,0,49) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(30)+ 10);

        bFound = TRUE;

      }

      /*

      sTemplate = "g_i_progspike01";

      if(SWTR_InRange(iRoll,40,49) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,50,59) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      */

      sTemplate = "G_I_MEDEQPMNT02";

      if(SWTR_InRange(iRoll,50,69) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE001";

      if(SWTR_InRange(iRoll,70,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE002";

      if(SWTR_InRange(iRoll,80,89) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE003";

      if(SWTR_InRange(iRoll,90,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 7:  //high level corpse container

      sTemplate = "G_I_CREDITS001";

      if(SWTR_InRange(iRoll,0,49) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(60)+ 40);

        bFound = TRUE;

      }

      /*

      sTemplate = "g_i_progspike01";

      if(SWTR_InRange(iRoll,40,49) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,50,59) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      */

      sTemplate = "G_I_MEDEQPMNT03";

      if(SWTR_InRange(iRoll,50,69) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE004";

      if(SWTR_InRange(iRoll,70,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE005";

      if(SWTR_InRange(iRoll,80,89) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE006";

      if(SWTR_InRange(iRoll,90,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 8:  //low level shadowlands container

      sTemplate = "G_I_CREDITS001";

      if(SWTR_InRange(iRoll,0,69) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(20)+ 1);

        bFound = TRUE;

      }

      /*

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,60,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      */

      sTemplate = "g_i_medeqpmnt01";

      if(SWTR_InRange(iRoll,70,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 9:  //mid level shadowlands container

      sTemplate = "G_I_CREDITS001";

      if(SWTR_InRange(iRoll,0,59) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(30)+ 10);

        bFound = TRUE;

      }

      /*

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,50,59) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      */

      sTemplate = "g_i_medeqpmnt02";

      if(SWTR_InRange(iRoll,60,69) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE001";

      if(SWTR_InRange(iRoll,70,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE002";

      if(SWTR_InRange(iRoll,80,89) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE003";

      if(SWTR_InRange(iRoll,90,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 10:  //high level shadowlands container

      sTemplate = "G_I_CREDITS001";

      if(SWTR_InRange(iRoll,0,59) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(60)+ 40);

        bFound = TRUE;

      }

      /*

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,50,59) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      */

      sTemplate = "g_i_medeqpmnt03";

      if(SWTR_InRange(iRoll,60,69) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE004";

      if(SWTR_InRange(iRoll,70,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE005";

      if(SWTR_InRange(iRoll,80,89) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE006";

      if(SWTR_InRange(iRoll,90,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 11:  //low level droid container

      /*

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,0,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      */

      sTemplate = "G_I_DRDLTPLAT001";

      if(SWTR_InRange(iRoll,0,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_DRDMTNSEN001";

      if(SWTR_InRange(iRoll,80,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 12:  //mid level droid container

      /*

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,0,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      */

      sTemplate = "G_I_DRDLTPLAT002";

      if(SWTR_InRange(iRoll,0,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_DRDMTNSEN002";

      if(SWTR_InRange(iRoll,80,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 13:  //high level droid container

    /*

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,0,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      */

      sTemplate = "G_I_DRDLTPLAT003";

      if(SWTR_InRange(iRoll,0,79) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_DRDMTNSEN003";

      if(SWTR_InRange(iRoll,80,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 14:  //rakatan container

    /*

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,0,15) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      sTemplate = "g_i_progspike01";

      if(SWTR_InRange(iRoll,16,31) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(4)+ 3);

        bFound = TRUE;

      }

      */

      sTemplate = "G_I_DRDREPEQP003";

      if(SWTR_InRange(iRoll,0,24) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE004";

      if(SWTR_InRange(iRoll,25,49) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE005";

      if(SWTR_InRange(iRoll,50,74) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE006";

      if(SWTR_InRange(iRoll,75,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    case 15:  //sandperson container

    /*

      sTemplate = "g_i_parts01";

      if(SWTR_InRange(iRoll,0,11) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      */

      sTemplate = "g_w_fraggren01";

      if(SWTR_InRange(iRoll,0,23) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      sTemplate = "G_w_StunGren01";

      if(SWTR_InRange(iRoll,24,35) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      sTemplate = "G_w_SonicGren01";

      if(SWTR_InRange(iRoll,36,47) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      sTemplate = "g_w_iongren01";

      if(SWTR_InRange(iRoll,48,59) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate + SWTR_GetQuantity(Random(3)+ 2);

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE001";

      if(SWTR_InRange(iRoll,60,71) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE002";

      if(SWTR_InRange(iRoll,72,83) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      sTemplate = "G_I_ADRNALINE003";

      if(SWTR_InRange(iRoll,84,99) && SWTR_IsUnique(sTemplate,sFilter))

      {

        sObjDesc = sTemplate;

        bFound = TRUE;

      }

      break;

    }

  } while(!bFound);

  return(sObjDesc);

}



//Fill an object with treasure from the specified table

//This is the only function that should be used outside this include file

void SWTR_PopulateTreasure(object oContainer,int iTable,int iItems = 1,int bUnique = TRUE)

{

  string sFilter = "";  //maintains list of item templates already retrieved

  string sItem,sTemplate;

  int iQuantity;

  int i;



  if(!GetIsObjectValid(oContainer))

  {

    SWTR_Debug_PostString("invalid container");

    return;

  }



  while(iItems > 0)

  {

    sItem = SWTR_GetTreasure(iTable,sFilter);

    if(sItem == "")

    {

      SWTR_Debug_PostString("bad table");

    }

    //parse the item description

    //treasure blobs (strings) consist of the item template followed by the quantity

    if((i = FindSubString(sItem,"[")) >= 0)

    {

      iQuantity = StringToInt(GetSubString(sItem,i+1,4));

      sTemplate = GetSubString(sItem,0,i);

    }

    else

    {

      iQuantity = 1;

      sTemplate = sItem;

    }

    //create item

    if(!GetIsObjectValid(CreateItemOnObject(sTemplate,oContainer,iQuantity)))

    {

      SWTR_Debug_PostString("item create failed (" + sTemplate + ")");

    }

    else

    {

      SWTR_Debug_PostString("container:" + GetTag(oContainer) + " item:" + sTemplate,FALSE);

    }

    //update our filter if we are maintaining uniqueness

    if(bUnique)

    {

      sFilter = sFilter + sTemplate;

    }

    iItems--;

  }

}

''',

    'k_inc_unk': b'''//::///////////////////////////////////////////////

//:: k_inc_unk

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

  include file for unknown world

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: Sept. 9, 2002

//:://////////////////////////////////////////////

#include "k_inc_debug"

#include "k_inc_utility"

#include "k_inc_generic"

//mark an object for cleanup by the UNK_CleanupDeadObjects function

void UNK_MarkForCleanup(object obj);



//destroy all objects whose PLOT_10 flag has been set

void UNK_CleanupDeadObjects(object oArea);



//mark object for cleanup and move to nearest exit

void UNK_LeaveArea(object obj = OBJECT_SELF, int bRun = FALSE);



//test if red rakata are hostile

int UNK_GetRedRakataHostile();



//test if black rakata are hostile

int UNK_GetBlackRakataHostile();



//make red rakatans hostile

void UNK_SetRedRakataHostile();



//make black rakatans hostile

void UNK_SetBlackRakataHostile();



//make black rakatans neutral

void UNK_SetBlackRakataNeutral();



//fill container with treasure from table

void UNK_AddTreasureToContainer(object oContainer,int iTable,int iAmount);



// unavoidable damage to all within radius

void UNK_RakDefence(string sObjectTag, float fDistance, int bIndiscriminant = TRUE);



//::///////////////////////////////////////////////

//:: UNK_MarkForCleanup

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//mark an object for cleanup by the TAR_CleanupDeadObjects function

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 26, 2002

//:://////////////////////////////////////////////

void UNK_MarkForCleanup(object obj)

{

  UT_SetPlotBooleanFlag(obj,SW_PLOT_BOOLEAN_10,TRUE);

}



//::///////////////////////////////////////////////

//:: UNK_CleanupDeadObjects

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//destroy all objects whose PLOT_10 flag has been set

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 15, 2002

//:://////////////////////////////////////////////

void UNK_CleanupDeadObjects(object oArea)

{

  object obj;



  obj = GetFirstObjectInArea(oArea);

  //Db_PostString("START CLEANUP...",5,7,5.0);

  while(GetIsObjectValid(obj))

  {

    //Db_PostString("FOUND OBJ",5,6,5.0);

    if ((UT_GetPlotBooleanFlag(obj,SW_PLOT_BOOLEAN_10)) && (IsObjectPartyMember(obj) == FALSE))

    {

      //Db_PostString("CLEANING UP OBJECT",5,5,5.0);

      DestroyObject(obj,0.0,TRUE);

    }

    obj = GetNextObjectInArea(oArea);

  }

}



//::///////////////////////////////////////////////

//:: UNK_LeaveArea

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//mark object for cleanup and move to nearest exit

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 26, 2002

//:://////////////////////////////////////////////

void UNK_LeaveArea(object obj = OBJECT_SELF, int bRun = FALSE)

{

  object oExit = GetNearestObjectByTag("punk_wpnpcext");



  UNK_MarkForCleanup(obj);

  if ((GetIsObjectValid(oExit)) && (IsObjectPartyMember(oExit) == FALSE))

  {

    UT_PlotMoveObject(oExit,bRun);

  }

}



//::///////////////////////////////////////////////

//:: UNK_GetRedRakataHostile

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//test if red rakata are hostile

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: Sept. 10, 2002

//:://////////////////////////////////////////////

int UNK_GetRedRakataHostile()

{

  return (GetGlobalNumber("unk_redvill") == 99);

}



//::///////////////////////////////////////////////

//:: UNK_GetBlackRakataHostile

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//test if black rakata are hostile

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: Sept. 10, 2002

//:://////////////////////////////////////////////

int UNK_GetBlackRakataHostile()

{

  return ((GetGlobalBoolean("UNK_USEDDARKSIDE") == FALSE) && (GetGlobalBoolean("UNK_BLACKHOSTILE") == FALSE));

}



//::///////////////////////////////////////////////

//:: UNK_SetRedRakatanHostile

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//make red rakatans hostile

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: Sept. 13, 2002

//:://////////////////////////////////////////////

void UNK_SetRedRakataHostile()

{

  object obj;



  SetGlobalNumber("Unk_redvill",99);

  SetGlobalBoolean("Unk_RedHostile",TRUE);

  obj = GetFirstObjectInArea();

  while (GetIsObjectValid(obj))

  {

    if ((GetTag(obj) != "unk42_breed01") && (GetTag(obj) != "unk42_breed02") && (GetTag(obj) != "unk42_breed03") && (GetTag(obj) != "unk41_gizka") && (IsObjectPartyMember(obj) == FALSE))

    {

      ChangeToStandardFaction(obj,STANDARD_FACTION_HOSTILE_1);

      AssignCommand(obj,ClearAllActions());

      AssignCommand(obj, GN_DetermineCombatRound());

    }

    obj = GetNextObjectInArea();

  }

}



//::///////////////////////////////////////////////

//:: UNK_SetBlackRakatanHostile

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//make black rakatans hostile

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: Sept. 13, 2002

//:://////////////////////////////////////////////

void UNK_SetBlackRakataHostile()

{

  object obj;



  Db_PostString("SCANNING...",5,5,5.0);

  SetGlobalBoolean("UNK_BLACKHOSTILE",TRUE);

  obj = GetFirstObjectInArea();

  Db_PostString("FOUND OBJ...",5,5,5.0);

  while(GetIsObjectValid(obj))

  {

    if ((GetTag(obj) != "unk41_gizka") && (IsObjectPartyMember(obj) == FALSE) && (GetTag(obj) != "unk43_redpris"))

    {

      Db_PostString("IN LOOP...",5,5,5.0);

      Db_PostString("RAKATA HOSTILE",5,5,5.0);

      ChangeToStandardFaction(obj,STANDARD_FACTION_HOSTILE_1);

      AssignCommand(obj,ClearAllActions());

      AssignCommand(obj, GN_DetermineCombatRound());

    }



    obj = GetNextObjectInArea();

  }

}



//::///////////////////////////////////////////////

//:: UNK_SetBlackRakataNeutral

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//make black rakatans neutral

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: Sept. 13, 2002

//:://////////////////////////////////////////////

void UNK_SetBlackRakataNeutral()

{

  object obj;



  obj = GetFirstObjectInArea();

  while(GetIsObjectValid(obj))

  {

    if (IsObjectPartyMember(obj) == FALSE)

    {

        ChangeToStandardFaction(obj,STANDARD_FACTION_NEUTRAL);

        AssignCommand(obj,ClearAllActions());

    }



    obj = GetNextObjectInArea();

  }

}



//fill container with treasure from table

void UNK_AddTreasureToContainer(object oContainer,int iTable,int iAmount)

{

  int i;



  if(!GetIsObjectValid(oContainer))

  {

    return;

  }



  for(i = 0;i < iAmount;i++)

  {

    switch(iTable)

    {

    case 0:

      switch(Random(3))

      {

      case 0:

        CreateItemOnObject("G_I_CREDITS001",oContainer,Random(50) + 20);

        break;

      case 1:

        CreateItemOnObject("G_I_MEDEQPMNT04",oContainer);

        break;

      default:

        CreateItemOnObject("G_I_MEDEQPMNT02",oContainer);

      }

      break;

    case 1:

      switch(Random(5))

      {

      case 0:

        CreateItemOnObject("G_I_CREDITS001",oContainer,Random(50) + 20);

        break;

      case 1:

        CreateItemOnObject("G_I_MEDEQPMNT04",oContainer);

        break;

      case 2:

        CreateItemOnObject("G_I_DRDREPEQP002",oContainer);

        break;

      case 3:

        CreateItemOnObject("G_I_PARTS01",oContainer);

        break;

      default:

        CreateItemOnObject("G_I_MEDEQPMNT02",oContainer);

      }

      break;

    }

  }

}





//::///////////////////////////////////////////////

//:: Rakatan Defence Grid

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Overloads a power conduit and does 10d6 damage

    to all within the specified radius

*/

//:://////////////////////////////////////////////

//:: Created By: Peter Thomas

//:: Created On:

//:://////////////////////////////////////////////



void UNK_RakDefence(string sObjectTag, float fDistance, int bIndiscriminant = TRUE)

{

    object oWay = GetObjectByTag(sObjectTag);

    if(GetIsObjectValid(oWay))

    {

        effect eFNF = EffectVisualEffect(VFX_FNF_GRENADE_ION);

        effect eVFXHit = EffectVisualEffect(1021);

        effect eVFXBeam = EffectBeam(VFX_BEAM_LIGHTNING_DARK_L, oWay, BODY_NODE_CHEST);

        effect eDam;



        object oTarget = GetNearestObject(OBJECT_TYPE_CREATURE, oWay, 1);

        int nCount = 1;

        int nDam = 1000;

        float fDelay = 0.3;



        AssignCommand(oWay, ActionPlayAnimation(ANIMATION_PLACEABLE_OPEN));



        DelayCommand(0.3, ApplyEffectAtLocation(DURATION_TYPE_INSTANT, eFNF, GetLocation(oWay)));

        while(GetIsObjectValid(oTarget) && GetDistanceBetween(oTarget, oWay) <= fDistance)

        {

            if(bIndiscriminant == TRUE || GetIsEnemy(oTarget, GetFirstPC()))

            {

                eDam = EffectDamage(nDam, DAMAGE_TYPE_UNIVERSAL);

                DelayCommand(fDelay, ApplyEffectToObject(DURATION_TYPE_INSTANT, eDam, oTarget));

                //fDelay = fDelay + 0.17;



                eDam = EffectDeath();

                DelayCommand(fDelay + 0.1, ApplyEffectToObject(DURATION_TYPE_INSTANT, eDam, oTarget));

                DelayCommand(fDelay, ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eVFXBeam, oTarget, 1.0));

                DelayCommand(fDelay, ApplyEffectToObject(DURATION_TYPE_INSTANT, eVFXHit, oTarget, 1.0));

                fDelay = fDelay + 0.17;

}

            nCount++;

            oTarget = GetNearestObject(OBJECT_TYPE_CREATURE, oWay, nCount);

        }

        ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(VFX_PRO_DROID_KILL), oWay);



    }

}



''',

    'k_inc_utility': b'''//:: k_inc_utility

/*

    common functions used throughout various scripts



    Modified by Peter T. 17/03/03

    - Added UT_MakeNeutral2(), UT_MakeHostile1(), UT_MakeFriendly1() and UT_MakeFriendly2()

*/

//:: Created By: Jason Booth

//:: Copyright (c) 2002 Bioware Corp.



// Plot Flag Constants.

int SW_PLOT_BOOLEAN_01 = 0;

int SW_PLOT_BOOLEAN_02 = 1;

int SW_PLOT_BOOLEAN_03 = 2;

int SW_PLOT_BOOLEAN_04 = 3;

int SW_PLOT_BOOLEAN_05 = 4;

int SW_PLOT_BOOLEAN_06 = 5;

int SW_PLOT_BOOLEAN_07 = 6;

int SW_PLOT_BOOLEAN_08 = 7;

int SW_PLOT_BOOLEAN_09 = 8;

int SW_PLOT_BOOLEAN_10 = 9;

int SW_PLOT_HAS_TALKED_TO = 10;

int SW_PLOT_COMPUTER_OPEN_DOORS = 11;

int SW_PLOT_COMPUTER_USE_GAS = 12;

int SW_PLOT_COMPUTER_DEACTIVATE_TURRETS = 13;

int SW_PLOT_COMPUTER_DEACTIVATE_DROIDS = 14;

int SW_PLOT_COMPUTER_MODIFY_DROID = 15;

int SW_PLOT_REPAIR_WEAPONS = 16;

int SW_PLOT_REPAIR_TARGETING_COMPUTER = 17;

int SW_PLOT_REPAIR_SHIELDS = 18;

int SW_PLOT_REPAIR_ACTIVATE_PATROL_ROUTE = 19;



// UserDefined events

int HOSTILE_RETREAT = 1100;



//Alignment Adjustment Constants

int SW_CONSTANT_DARK_HIT_HIGH = -6;

int SW_CONSTANT_DARK_HIT_MEDIUM = -5;

int SW_CONSTANT_DARK_HIT_LOW = -4;

int SW_CONSTANT_LIGHT_HIT_LOW = -2;

int SW_CONSTANT_LIGHT_HIT_MEDIUM = -1;

int SW_CONSTANT_LIGHT_HIT_HIGH = 0;



// Returns a pass value based on the object's level and DC rating of 0, 1, or 2 (easy, medium, difficult)

// December 20 2001: Changed so that the difficulty is determined by the

// NPC's Hit Dice

int AutoDC(int DC, int nSkill, object oTarget);

//  checks for high charisma

int IsCharismaHigh();

//  checks for low charisma

int IsCharismaLow();

//  checks for normal charisma

int IsCharismaNormal();

//  checks for high intelligence

int IsIntelligenceHigh();

//  checks for low intelligence

int IsIntelligenceLow();

//  checks for normal intelligence

int IsIntelligenceNormal();

//  checks to see if pc is very dark side

int IsDarkHigh();

//  checks to see if pc is just a little dark side

int IsDarkLow();

//  checks to see if pc is dark side

int IsDark();

//  checks to see if pc is very light side

int IsLightHigh();

//  checks to see if pc is slightly light side

int IsLightLow();

//  checks to see if pc is light side

int IsLight();

//  checks to see if pc is neutral

int IsNeutral();

//  pads a string with the given pad character to the specified length

string PadString(string str = "",string pad = " ",int length = 0);

//  causes the given object to initiate conversation with the player

void TalkToPC(object oSpeaker);

//Gets the boolean state of a plot bit field

int UT_GetPlotBooleanFlag(object oTarget, int nIndex);

//Sets the boolean state of plot bit field using the SW_PLOT_BOOLEAN CONSTANTS

void UT_SetPlotBooleanFlag(object oTarget, int nIndex, int nState);

//Determines state of the HAS TALKED TO FLAG on the passed in object.

int UT_GetTalkedToBooleanFlag(object oTarget);

//Sets the Talked To Flag on the specified object.

void UT_SetTalkedToBooleanFlag(object oTarget, int nState = TRUE);

//Get the nearest PC to the specified object

object UT_GetNearestPCToObject(object oTarget = OBJECT_SELF);

//Determine if object is a PC

int UT_IsObjectPC(object oTarget = OBJECT_INVALID);

//does a heavy darkside adjustment on the player

void UT_DarkHigh(object oTarget);

//does a medium darkside adjustment on the player

void UT_DarkMed(object oTarget);

//does a small darkside adjustment on the player

void UT_DarkSml(object oTarget);

//does a heavy lightside adjustment on the player

void UT_LightHigh(object oTarget);

//does a medium lightside adjustment on the player

void UT_LightMed(object oTarget);

//does a small lightside adjustment on the player

void UT_LightSml(object oTarget);

//Resets all of an objects Bit Fields to TRUE or FALSE

void UT_ResetPlotBooleanFlags(object oToChange, int nState);

//make object do an uninterruptible path move

void UT_PlotMovePath(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE);

//make object do an uninterruptible move to an object

void UT_PlotMoveObject(object oTarget,int nRun = FALSE);

//make object do an uninterruptible move to a location

void UT_PlotMoveLocation(location lTarget,int nRun = FALSE);

//perform a skill check

int UT_SkillCheck(int iDC, int iSkill, object oTarget);

//test whether force power is dark side

int UT_IsDarkSidePower(int iSpellID);

//Creates an object at a location without having to pass back an object.  Can be

//used in DelayCommand functions.

void UT_CreateObject(int nObjectType, string sTemplate, location lLocal);

//Command used in the swoop droid triggers to activate the spawning in of messengers.

void UT_SpawnMessenger();

//Makes the NPC flee to an SW_EXIT waypoint and destroy itself

void UT_ExitArea(int nRun = FALSE);

//Determines the number of spikes or parts to take away from the PC.

int UT_DeterminesItemCost(int nDC, int nSkill);

//Remove a number of computer spikes.

void UT_RemoveComputerSpikes(int nNumber);

//Remove a number of parts

void UT_RemoveRepairParts(int nNumber);

//Return items amounts for either the Spikes or the Parts

int UT_ReturnSpikePartAmount(int nSkill);

//Searches the area and changes all turrets with the specified tag to the neutral faction

void UT_MakeNeutral(string sObjectTag);

//Searches the area and changes all droids with the specified tag to the insane faction

void UT_MakeInsane(string sObjectTag);

//Searches through the ara and stuns all droids with the given tag permanently

void UT_StunDroids(string sObjectTag);

//Starts a fight

void UT_StartCombat(object oObject);

//Releases gas into the room and kills all biologicals in the specified radius

//The radius should be between 2 - 5m

void UT_GasRoom(string sWayTag, float fDistance, int bIndiscriminant = TRUE);

//Overloads a power conduit and does 10d6 damage to all within the specified radius

//bIndiscriminant: TRUE-affects all creatures; FALSE-affects only enemies

void UT_OverloadConduit(string sObjectTag, float fDistance, int bIndiscriminant = TRUE);

//Returns a creature to the nearest "wp_" waypoint.

//During this time the creature will be uncommanable

void UT_ReturnToBase(string sTag = "wp_homebase");

//NPC initiates a conversation with the player.

void UT_NPC_InitConversation(string sNPCTag,string sDlg = "",object oEntered = OBJECT_INVALID);

//Sets the Journal entry for the starmap automatically.

void UT_SetStarmapJournal();

//Creates number of creatures with a specific template at a specified waypoint tag.

//Total is the number times the loop will run.

//fTimeDelay is the number seconds between iterations.

//nSpawnIncrement is the number of templates spawned in per iteration.

void UT_RunCombatEncounter(string sTemplate, string sTag, int nTotal = 3, float fTimeDelay = 1.5, int nSpawnIncrement = 1);

//Sets the talik to flag on all objects with the specified tag using the PC as a focal point.

void UT_SetTalkToFlagByTag(string sTag);

//Locks any other doors with the same tag.  Makes them plot.

void UT_LockDoorDuplicates(string sTag);

//Check to see if the Party member specified is in the party and within the distance given.

int UT_CheckCanPartyMemberInterject(int nNPC_Constant, float fDistance);

//Reinitializes the Party Planet Initialization Variables

void UT_ReinitializePartyPlanetVariables();

//Teleport a party member

void UT_TeleportPartyMember(object oPartyMember, location lDest);

//Returns true if oTarget is the object of interest of an attacker

int UT_GetUnderAttack(object oTarget);

//Teleport the whole party and face them the direction that the objects they

//are being jumped to are facing.

void UT_TeleportWholeParty(object oWP0, object oWP1, object oWP2);

//Pause and restart a conversation.

void UT_ActionPauseConversation(float fDelay);

//Spawn NPC without return

void UT_SpawnAvailableNPC(int nNPC, location lWay);

//Goes through the current party and heals them.

void UT_HealParty();

//Heals the object passed in.

void UT_HealNPC(object oNPC);

//Heals all of the Party NPCs in Area

void UT_HealAllPartyNPCs();

//This function removes party members. It stores the npc constants of the removed party members.

void UT_StoreParty();

//This function restore party members. It will only restore party members removed via the UT_StoreParty funcion

void UT_RestoreParty();

//Returns the NPC code for the given object if it is a NPC, otherwise it returns -1

int UT_GetNPCCode(object oNPC);

//restores all party mambers to 1 hp if tempoarily dead

void UT_RestorePartyToOneHealth();

//Alter the stack size of a given item

void UT_AlterItemStack(object oItem,int iNum = 1,int bDecrement = TRUE);

//Goes through the party and removes them. This is best used on Module Load when the object are not actually created yet.

void UT_ClearAllPartyMembers();

//Does a DC check just using an ability score

int UT_AbilityCheck(int iDC, int iAbility, object oTarget);

//Validate a jump back to the last location by comparing module names.

int UT_ValidateJump(string sLastModule);

//Make alignment change based on a constant passed in to the function

void UT_AdjustCharacterAlignment(object oTarget, int nScale);



// Added by Peter T. 17/03/03

// Searches the area and changes all instances with the specified tag to the Neutral faction

void UT_MakeNeutral2(string sObjectTag);

// Added by Peter T. 17/03/03

// Searches the area and changes all instances with the specified tag to the Hostile_1 faction

void UT_MakeHostile1(string sObjectTag);

// Added by Peter T. 17/03/03

// Searches the area and changes all instances with the specified tag to the Friendly_1 faction

void UT_MakeFriendly1(string sObjectTag);

// Added by Peter T. 17/03/03

// Searches the area and changes all instances with the specified tag to the Friendly_2 faction

void UT_MakeFriendly2(string sObjectTag);

//performs a standard torture cage effect

void UT_ActivateTortureCage(object oCage, object oTarget,float fDuration);

//Makes the animal face the PC, do its victory and play a sound passed in.

//Should be used in conjunction with the k_def_interact spawn in

void UT_DoAmbientReaction(string sSound);





//STAR MAP FUNCTION SET

//Advances K_STAR_MAP, sets the journal and sets the talk to flag.

void UT_StarMap1VariableSet();

//Plays the animations necessary for the current state of the starmap variable

void UT_StarMap2PlayAnimation();

//Returns the appropriate animation loop for the Star Map

int UT_StarMap3GetLoopAnim(int nStarMapVar);

//Runs the entire Starmap sequence as a black box with no extra scripting required.

void UT_StarMap4RunStarMap();







///////////////////////////////////////////////////////////////////////////////

/*

    AutoDC



Relation to Max Persuade   Low Persaude chance   Mid Persuade chance   High Persuade chance



Higher than Max                  100                   100                     100

75% to 100%                      100                   100                     75

50% to 75%                       75                    50                      25

25% to 50%                       50                    25                      0

0% to 25%                        25                    0                       0

*/

///////////////////////////////////////////////////////////////////////////////

//  Returns a pass value based on the object's level and the suggested DC

// December 20 2001: Changed so that the difficulty is determined by the

// NPC's Hit Dice

///////////////////////////////////////////////////////////////////////////////

//  Created By: Preston Watamaniuk

///////////////////////////////////////////////////////////////////////////////

int AutoDC(int DC, int nSkill, object oTarget)

{

    int nSkillLvl = GetSkillRank(nSkill, oTarget);

    int nMax;

    int nRoll = d100();



    nMax = GetHitDice(oTarget) + 5;

    float fMax = IntToFloat(nMax);

    float fSkillLvl = IntToFloat(nSkillLvl);

    float fPercent = fSkillLvl/fMax;



    AurPostString("Skill Percentage Chance = " + FloatToString(fPercent,4,2),5,5,3.0);

    AurPostString("Percentage Die Roll     = " + IntToString(nRoll),5,7,3.0);



    if(fPercent <= 0.25)

    {

        if(DC == 0 && nRoll <= 40){return TRUE;}

    }

    else if(fPercent > 0.25 && fPercent <= 0.5)

    {

        if(DC == 0 && nRoll <= 50){return TRUE;}

        if(DC == 1 && nRoll <= 25){return TRUE;}

    }

    else if(fPercent > 0.5 && fPercent <= 0.75)

    {

        if(DC == 0 && nRoll <= 75){return TRUE;}

        if(DC == 1 && nRoll <= 50){return TRUE;}

        if(DC == 2 && nRoll <= 25){return TRUE;}

    }

    else if(fPercent > 0.75 && fPercent <= 1.0)

    {

        if(DC == 0 && nRoll <= 100){return TRUE;}

        if(DC == 1 && nRoll <= 100){return TRUE;}

        if(DC == 2 && nRoll <= 75){return TRUE;}

    }

    else if(fPercent > 1.0)

    {

        return TRUE;

    }

    return FALSE;





    //LEGACY CODE CHANGED ON FEB 18, 2003

    /*

    Easy = Lvl/4 ...rounded up

    Moderate = 3/Lvl + Lvl ...rounded up

    Difficult = Lvl * 1.5 + 6 ...rounded up



    int nLevel = GetHitDice(OBJECT_SELF);

    if(nLevel <= 0 || nLevel > 20)

    {

        nLevel = GetHitDice(GetPCSpeaker());

    }

    int nTest = 0;

    switch (DC)

    {

    case 0: nTest = nLevel / 4 + 1; break;

        // * minor tweak to lower the values a little

    case 1: nTest = (3 / nLevel + nLevel) - abs( (nLevel/2) -2); break;

    case 2: nTest = FloatToInt(nLevel * 1.5 + 6) - abs( ( FloatToInt(nLevel/1.5) -2));   break;

    }

    //SpeakString(IntToString(nTest));



    // * Roll d20 + skill rank vs. DC + 10

    if (GetSkillRank(nSkill, oTarget) + d20() >= nTest + 10)

    {

       return TRUE;

    }

       return FALSE;

    */

}



//::///////////////////////////////////////////////

//:: IsCharismaHigh

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks for high charisma

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsCharismaHigh()

{

  if (GetAbilityScore(GetPCSpeaker(),ABILITY_CHARISMA) >= 15)

  {

    return TRUE;

  }

  else

  {

    return FALSE;

  }

}



//::///////////////////////////////////////////////

//:: IsCharismaLow

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks for low charisma

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsCharismaLow()

{

  return !IsCharismaNormal();

}



//::///////////////////////////////////////////////

//:: IsCharismaNormal

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks for normal charisma

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsCharismaNormal()

{

  if (GetAbilityScore(GetPCSpeaker(),ABILITY_CHARISMA) >= 10)

  {

    return TRUE;

  }

  else

  {

    return FALSE;

  }

}



//::///////////////////////////////////////////////

//:: IsIntelligenceHigh

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks for high intelligence

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsIntelligenceHigh()

{

  if (GetAbilityScore(GetPCSpeaker(),ABILITY_INTELLIGENCE) >= 15)

  {

    return TRUE;

  }

  else

  {

    return FALSE;

  }

}



//::///////////////////////////////////////////////

//:: IsIntelligenceLow

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks for low intelligence

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsIntelligenceLow()

{

  return !IsIntelligenceNormal();

}



//::///////////////////////////////////////////////

//:: IsIntelligenceNormal

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks for normal intelligence

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsIntelligenceNormal()

{

  if (GetAbilityScore(GetPCSpeaker(),ABILITY_INTELLIGENCE) >= 10)

  {

    return TRUE;

  }

  else

  {

    return FALSE;

  }

}



//::///////////////////////////////////////////////

//:: IsDarkHigh

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks to see if pc is very dark side

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsDarkHigh()

{

    int align = GetGoodEvilValue(GetPCSpeaker());



    if(align >= 0 && align < 20)

    {

        return TRUE;

    }

    else

    {

        return FALSE;

    }

}



//::///////////////////////////////////////////////

//:: IsDarkLow

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks to see if pc is just a little dark side

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsDarkLow()

{

    int align = GetGoodEvilValue(GetPCSpeaker());



    if(align >= 20 && align < 40)

    {

        return TRUE;

    }

    else

    {

        return FALSE;

    }

}



//::///////////////////////////////////////////////

//:: IsDark

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks to see if pc is dark side

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsDark()

{

    if(IsDarkLow() || IsDarkHigh())

    {

        return TRUE;

    }

    else

    {

        return FALSE;

    }

}



//::///////////////////////////////////////////////

//:: IsLightHigh

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks to see if pc is very light side

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsLightHigh()

{

    int align = GetGoodEvilValue(GetPCSpeaker());



    if(align >= 81)

    {

        return TRUE;

    }

    else

    {

        return FALSE;

    }

}



//::///////////////////////////////////////////////

//:: IsLightLow

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks to see if pc is slightly light side

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsLightLow()

{

    int align = GetGoodEvilValue(GetPCSpeaker());



    if(align >= 61 && align < 81)

    {

        return TRUE;

    }

    else

    {

        return FALSE;

    }

}



//::///////////////////////////////////////////////

//:: IsLight

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks to see if pc is light side

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsLight()

{

    if(IsLightLow() || IsLightHigh())

    {

        return TRUE;

    }

    else

    {

        return FALSE;

    }

}



//::///////////////////////////////////////////////

//:: IsNeutral

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  checks to see if pc is neutral

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 19, 2002

//:://////////////////////////////////////////////

int IsNeutral()

{

    if(!IsDark() && !IsLight())

    {

        return TRUE;

    }

    else

    {

        return FALSE;

    }

}



//::///////////////////////////////////////////////

//:: PadString

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  pads a string with the given pad character to the specified length

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  June 20, 2002

//:://////////////////////////////////////////////

string PadString(string str = "",string pad = " ",int length = 0)

{

  while(GetStringLength(str) < length)

  {

    str = pad + str;

  }

  return(str);

}



//::///////////////////////////////////////////////

//:: TalkToPC

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//  causes the given object to initiate conversation with the player

*/

//:://////////////////////////////////////////////

//:: Created By:  Jason Booth

//:: Created On:  July 12, 2002

//:://////////////////////////////////////////////

void TalkToPC(object oSpeaker)

{

  AssignCommand(oSpeaker,ClearAllActions());

  AssignCommand(oSpeaker,

  ActionStartConversation(GetNearestCreature(CREATURE_TYPE_PLAYER_CHAR, PLAYER_CHAR_IS_PC)));

}



//::///////////////////////////////////////////////

//:: Get Boolean Plot Flag

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Gets the boolean state of a plot bit field

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: July 15, 2002

//:://////////////////////////////////////////////

int UT_GetPlotBooleanFlag(object oTarget, int nIndex)

{

    int nPlotBoolean;

    if(nIndex >= 0 && nIndex <= 19 && GetIsObjectValid(oTarget))

    {

        nPlotBoolean = GetLocalBoolean(oTarget, nIndex);

        if(nPlotBoolean > 0)

        {

            return TRUE;

        }

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Set Boolean Plot Flag

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Sets the boolean state of a plot bit field

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: July 15, 2002

//:://////////////////////////////////////////////



void UT_SetPlotBooleanFlag(object oTarget, int nIndex, int nState)

{

    int nLevel = GetHitDice(GetFirstPC());

    if(nState == TRUE)

    {

        if(nIndex == SW_PLOT_COMPUTER_OPEN_DOORS ||

           nIndex == SW_PLOT_REPAIR_WEAPONS ||

           nIndex == SW_PLOT_REPAIR_TARGETING_COMPUTER ||

           nIndex == SW_PLOT_REPAIR_SHIELDS)

        {

            GiveXPToCreature(GetFirstPC(), nLevel * 15);

        }

        else if(nIndex == SW_PLOT_COMPUTER_USE_GAS || nIndex == SW_PLOT_REPAIR_ACTIVATE_PATROL_ROUTE || nIndex == SW_PLOT_COMPUTER_MODIFY_DROID)

        {

            GiveXPToCreature(GetFirstPC(), nLevel * 20);

        }

        else if(nIndex == SW_PLOT_COMPUTER_DEACTIVATE_TURRETS ||

                nIndex == SW_PLOT_COMPUTER_DEACTIVATE_DROIDS)

        {

            GiveXPToCreature(GetFirstPC(), nLevel * 10);

        }

    }

    if(nIndex >= 0 && nIndex <= 19 && GetIsObjectValid(oTarget))

    {

        if(nState == TRUE || nState == FALSE)

        {

            SetLocalBoolean(oTarget, nIndex, nState);

        }

    }

}



//::///////////////////////////////////////////////

//:: Get Talked To Flag

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns the state of the Talk to Flag

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: July 15, 2002

//:://////////////////////////////////////////////



int UT_GetTalkedToBooleanFlag(object oTarget)

{

    int nPlotFlag;

    if(GetIsObjectValid(oTarget))

    {

        nPlotFlag = GetLocalBoolean(oTarget, SW_PLOT_HAS_TALKED_TO);

        if(nPlotFlag > 0)

        {

            return TRUE;

        }

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Set Talked To Flag

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Sets the talked to flag to the given state.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: July 15, 2002

//:://////////////////////////////////////////////



void UT_SetTalkedToBooleanFlag(object oTarget, int nState = TRUE)

{

    if(GetIsObjectValid(oTarget))

    {

        if(nState == TRUE || nState == FALSE)

        {

            SetLocalBoolean(oTarget, SW_PLOT_HAS_TALKED_TO, nState);

        }

    }

}



//::///////////////////////////////////////////////

//:: UT_GetNearestPCToObject

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//Get the nearest PC to the specified object

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 15, 2002

//:://////////////////////////////////////////////

object UT_GetNearestPCToObject(object oTarget = OBJECT_SELF)

{

  return(GetNearestCreature(CREATURE_TYPE_PLAYER_CHAR, PLAYER_CHAR_IS_PC,oTarget));

}



//::///////////////////////////////////////////////

//:: UT_IsObjectPC

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//Determine if object is a PC

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 15, 2002

//:://////////////////////////////////////////////

int UT_IsObjectPC(object oTarget = OBJECT_INVALID)

{

  object oPC = GetFirstPC();



  while(oPC != OBJECT_INVALID)

  {

    if(oTarget == oPC)

    {

      return(TRUE);

    }

    oPC = GetNextPC();

  }



  return(FALSE);

}



//::///////////////////////////////////////////////

//:: Adjust Character Alignment

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Make alignment change based on a constant

    passed in to the function

    nDarkSide = 1 then do a darkside hit.

    nScale is the size of the hit. -3 to +3



    //Alignment Adjustment Constants



    int SW_CONSTANT_DARK_HIT_HIGH = -6;

    int SW_CONSTANT_DARK_HIT_MEDIUM = -5;

    int SW_CONSTANT_DARK_HIT_LOW = -4;

    int SW_CONSTANT_LIGHT_HIT_LOW = -2;

    int SW_CONSTANT_LIGHT_HIT_MEDIUM = -1;

    int SW_CONSTANT_LIGHT_HIT_HIGH = 0;



                    1       2       3         4      5

                    VLight  Light   Neutral   Dark   VDark

      High Light    2       4       6         8      10

      Mid Light     1       2       4         6      8

      Low Light     1       1       2         4      6

      Low Dark      -6      -4      -2        -1     -1

      Mid Dark      -8      -6      -4        -2     -1

      High Dark     -10     -8      -6        -4     -2

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 23, 2002

//:://////////////////////////////////////////////

void UT_AdjustCharacterAlignment(object oTarget, int nScale)

{

    //Find out if the target is good or evil

    int nScore = GetGoodEvilValue(oTarget);

    int nAlignType;

    //Set the type of alignment hit to do.

    if(nScale == SW_CONSTANT_DARK_HIT_HIGH ||

       nScale == SW_CONSTANT_DARK_HIT_MEDIUM ||

       nScale == SW_CONSTANT_DARK_HIT_LOW)

    {

        nAlignType = ALIGNMENT_DARK_SIDE;

    }

    else

    {

        nAlignType = ALIGNMENT_LIGHT_SIDE;

    }



    int nHit;

    int nAlignCategory;



    //Set the alignment category which will determine the base from which to calculate the hit.

    if(nScore >= 85)//VERY GOOD

    {

        nAlignCategory = 1;

    }

    else if(nScore < 85 && nScore > 60)//GOOD

    {

        nAlignCategory = 2;

    }

    else if(nScore <= 60 && nScore >= 40)//NEUTRAL

    {

        nAlignCategory = 3;

    }

    else if(nScore < 40 && nScore >= 15)//EVIL

    {

        nAlignCategory = 4;

    }

    else //VERY EVIL

    {

        nAlignCategory = 5;

    }



    //Calculate the hit.

    nHit = (nAlignCategory + nScale) * 2;

    if(nHit < 0)

    {

        nHit = nHit * -1;

    }

    if(nHit == 0)

    {

        nHit = 1;

    }

    //Zero results that do not mathematically fit within the formula.

    if(nAlignCategory == 1 && nScale == SW_CONSTANT_LIGHT_HIT_LOW)

    {

        nHit = 1;

    }

    else if(nAlignCategory == 5 && nScale == SW_CONSTANT_DARK_HIT_LOW)

    {

        nHit = 1;

    }

    AurPostString("Hit = " + IntToString(nHit), 5, 5, 4.0);

    

    AdjustAlignment(oTarget, nAlignType, nHit);

}



//::///////////////////////////////////////////////

//:: UT_DarkHigh

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//does a heavy darkside adjustment on the target

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 16, 2002

//:://////////////////////////////////////////////

void UT_DarkHigh(object oTarget)

{

    UT_AdjustCharacterAlignment(oTarget, SW_CONSTANT_DARK_HIT_HIGH);

    //AdjustAlignment(oTarget,ALIGNMENT_DARK_SIDE,10);

}

//::///////////////////////////////////////////////

//:: UT_DarkMed

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//does a medium darkside adjustment on the target

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 16, 2002

//:://////////////////////////////////////////////

void UT_DarkMed(object oTarget)

{

  UT_AdjustCharacterAlignment(oTarget, SW_CONSTANT_DARK_HIT_MEDIUM);

  //AdjustAlignment(oTarget,ALIGNMENT_DARK_SIDE,5);

}

//::///////////////////////////////////////////////

//:: UT_DarkSml

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//does a small darkside adjustment on the target

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 16, 2002

//:://////////////////////////////////////////////

void UT_DarkSml(object oTarget)

{

  UT_AdjustCharacterAlignment(oTarget, SW_CONSTANT_DARK_HIT_LOW);

  //AdjustAlignment(oTarget,ALIGNMENT_DARK_SIDE,1);

}

//::///////////////////////////////////////////////

//:: UT_LightHigh

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//does a heavy lightside adjustment on the target

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 16, 2002

//:://////////////////////////////////////////////

void UT_LightHigh(object oTarget)

{

  UT_AdjustCharacterAlignment(oTarget, SW_CONSTANT_LIGHT_HIT_HIGH);

  //AdjustAlignment(oTarget,ALIGNMENT_LIGHT_SIDE,10);

}

//::///////////////////////////////////////////////

//:: UT_LightMed

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//does a medium lightside adjustment on the target

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 16, 2002

//:://////////////////////////////////////////////

void UT_LightMed(object oTarget)

{

  UT_AdjustCharacterAlignment(oTarget, SW_CONSTANT_LIGHT_HIT_MEDIUM);

  //AdjustAlignment(oTarget,ALIGNMENT_LIGHT_SIDE,5);

}

//::///////////////////////////////////////////////

//:: UT_LightSml

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//does a small lightside adjustment on the target

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: July 16, 2002

//:://////////////////////////////////////////////

void UT_LightSml(object oTarget)

{

  UT_AdjustCharacterAlignment(oTarget, SW_CONSTANT_LIGHT_HIT_LOW);

  //AdjustAlignment(oTarget,ALIGNMENT_LIGHT_SIDE,1);

}



//::///////////////////////////////////////////////

//:: Reset Plot Booleans

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Goes through all of the plot bit fields and sets

    them to nState.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Aug 15, 2002

//:://////////////////////////////////////////////



void UT_ResetPlotBooleanFlags(object oToChange, int nState)

{

    int nCnt;

    for(nCnt; nCnt <= 9; nCnt++)

    {

        if(nState == TRUE || nState == FALSE)

        {

            SetLocalBoolean(oToChange, nCnt, nState);

        }

    }

}



//::///////////////////////////////////////////////

//:: Check Manaan Medical State

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns true if the manaan facilities have

    been destroyed.  Global = 4 returns true.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Aug 19, 2002

//:://////////////////////////////////////////////



int UT_GetIsKoltoDestroyed()

{

    return GetGlobalNumber("MAN_PLANET_PLOT") == 4;

}



//::///////////////////////////////////////////////

//:: UT_PlotMovePath

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//make object do an uninterruptible path move

//based on code done by Aidan (actually, pretty much a copy)

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 16, 2002

//:://////////////////////////////////////////////

void UT_PlotMovePath(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE)

{



    int nInc = 1;

    object oWP;

    int nIdx;

    if(nFirst > nLast)

    {

        nInc = -1;

    }

    for(nIdx = nFirst - nInc; abs(nLast - nIdx) > 0 && abs(nLast - nIdx) <= abs((nLast - nFirst) + 1); nIdx = nIdx + nInc)

    {

        oWP = GetObjectByTag(sWayPointTag + IntToString(nIdx + nInc));

        if(GetIsObjectValid(oWP))

        {

            ActionForceMoveToObject(oWP,nRun);

        }

    }

    ActionDoCommand(SetCommandable(TRUE));

    SetCommandable(FALSE);

}



//::///////////////////////////////////////////////

//:: UT_PlotMoveObject

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//make object do an uninterruptible move to an object

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 16, 2002

//:://////////////////////////////////////////////

void UT_PlotMoveObject(object oTarget,int nRun = FALSE)

{

  ActionForceMoveToObject(oTarget,nRun);

  ActionDoCommand(SetCommandable(TRUE));

  SetCommandable(FALSE);

}



//::///////////////////////////////////////////////

//:: UT_PlotMoveLocation

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//make object do an uninterruptible move to a location

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 16, 2002

//:://////////////////////////////////////////////

void UT_PlotMoveLocation(location lTarget,int nRun = FALSE)

{

  ActionForceMoveToLocation(lTarget,nRun);

  ActionDoCommand(SetCommandable(TRUE));

  SetCommandable(FALSE);

}



//::///////////////////////////////////////////////

//:: UT_SkillCheck

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//perform a skill check using a given DC

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: August 29, 2002

//:://////////////////////////////////////////////

int UT_SkillCheck(int iDC, int iSkill, object oTarget)

{

  if (GetSkillRank(iSkill, oTarget) + d20() >= iDC)

  {

    return TRUE;

  }

  return FALSE;

}



//::///////////////////////////////////////////////

//:: UT_IsDarkSidePower

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

//test whether force power is dark side

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: Sept. 11, 2002

//:://////////////////////////////////////////////

int UT_IsDarkSidePower(int iSpellID)

{

  if(iSpellID == FORCE_POWER_AFFECT_MIND) return(FALSE);

  if(iSpellID == FORCE_POWER_AFFLICTION) return(TRUE);

  if(iSpellID == FORCE_POWER_CHOKE) return(TRUE);

  if(iSpellID == FORCE_POWER_CURE) return(FALSE);

  if(iSpellID == FORCE_POWER_DEATH_FIELD) return(TRUE);

  if(iSpellID == FORCE_POWER_DOMINATE) return(TRUE);

  if(iSpellID == FORCE_POWER_DRAIN_LIFE) return(TRUE);

  if(iSpellID == FORCE_POWER_DROID_DESTROY) return(FALSE);

  if(iSpellID == FORCE_POWER_DROID_DISABLE) return(FALSE);

  if(iSpellID == FORCE_POWER_DROID_STUN) return(FALSE);

  if(iSpellID == FORCE_POWER_FEAR) return(TRUE);

  if(iSpellID == FORCE_POWER_FORCE_ARMOR) return(FALSE);

  if(iSpellID == FORCE_POWER_FORCE_AURA) return(FALSE);

  if(iSpellID == FORCE_POWER_FORCE_BREACH) return(FALSE);

  if(iSpellID == FORCE_POWER_FORCE_IMMUNITY) return(FALSE);

  if(iSpellID == FORCE_POWER_FORCE_JUMP) return(FALSE);

  if(iSpellID == FORCE_POWER_FORCE_JUMP_ADVANCED) return(FALSE);

  if(iSpellID == FORCE_POWER_FORCE_MIND) return(TRUE);

  if(iSpellID == FORCE_POWER_FORCE_PUSH) return(FALSE);

  if(iSpellID == FORCE_POWER_FORCE_SHIELD) return(FALSE);

  if(iSpellID == FORCE_POWER_FORCE_STORM) return(TRUE);

  if(iSpellID == FORCE_POWER_FORCE_WAVE) return(FALSE);

  if(iSpellID == FORCE_POWER_FORCE_WHIRLWIND) return(FALSE);

  if(iSpellID == FORCE_POWER_HOLD) return(FALSE);

  if(iSpellID == FORCE_POWER_HORROR) return(TRUE);

  if(iSpellID == FORCE_POWER_INSANITY) return(TRUE);

  if(iSpellID == FORCE_POWER_KILL) return(TRUE);

  if(iSpellID == FORCE_POWER_KNIGHT_SPEED) return(FALSE);

  if(iSpellID == FORCE_POWER_LIGHT_SABER_THROW) return(FALSE);

  if(iSpellID == FORCE_POWER_LIGHT_SABER_THROW_ADVANCED) return(FALSE);

  if(iSpellID == FORCE_POWER_LIGHTNING) return(TRUE);

  if(iSpellID == FORCE_POWER_MASTER_CONTROL) return(FALSE);

  if(iSpellID == FORCE_POWER_MASTER_SENSE) return(FALSE);

  if(iSpellID == FORCE_POWER_MIND_MASTERY) return(FALSE);

  if(iSpellID == FORCE_POWER_PLAGUE) return(FALSE);

  if(iSpellID == FORCE_POWER_REGENERATION) return(FALSE);

  if(iSpellID == FORCE_POWER_REGNERATION_ADVANCED) return(FALSE);

  if(iSpellID == FORCE_POWER_RESIST_COLD_HEAT_ENERGY) return(FALSE);

  if(iSpellID == FORCE_POWER_RESIST_FORCE) return(FALSE);

  if(iSpellID == FORCE_POWER_RESIST_POISON_DISEASE_SONIC) return(FALSE);

  if(iSpellID == FORCE_POWER_SHOCK) return(TRUE);

  if(iSpellID == FORCE_POWER_SLEEP) return(FALSE);

  if(iSpellID == FORCE_POWER_SLOW) return(FALSE);

  if(iSpellID == FORCE_POWER_SPEED_BURST) return(FALSE);

  if(iSpellID == FORCE_POWER_SPEED_MASTERY) return(FALSE);

  if(iSpellID == FORCE_POWER_STUN) return(FALSE);

  if(iSpellID == FORCE_POWER_SUPRESS_FORCE) return(FALSE);

  if(iSpellID == FORCE_POWER_WOUND) return(TRUE);



  return(FALSE);

}



//::///////////////////////////////////////////////

//:: UT_CreateObject

//:: Copyright (c) 2002 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Create an object without needing a variable

    to pass it into.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Sept. 21, 2002

//:://////////////////////////////////////////////

void UT_CreateObject(int nObjectType, string sTemplate, location lLocal)

{

    object oCreate = CreateObject(nObjectType, sTemplate, lLocal);

}



//::///////////////////////////////////////////////

//:: UT_JumpPartyToObject

//:: Copyright (c) 2002 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Move the entire party to the object specified.

*/

//:://////////////////////////////////////////////

//:: Created By: John Winski

//:: Created On: Sept. 24, 2002

//:://////////////////////////////////////////////

void UT_JumpPartyToObject(object oTarget)

{

    UT_RestorePartyToOneHealth();

    object oMember1 = GetPartyMemberByIndex(0);

    object oMember2 = GetPartyMemberByIndex(1);

    object oMember3 = GetPartyMemberByIndex(2);



    if (GetIsObjectValid(oMember1) == TRUE)

    {

        AssignCommand(oMember1, ClearAllActions());

        AssignCommand(oMember1, JumpToObject(oTarget));

    }

    if (GetIsObjectValid(oMember2) == TRUE)

    {

        AssignCommand(oMember2, ClearAllActions());

        AssignCommand(oMember2, JumpToObject(oTarget));

    }

    if (GetIsObjectValid(oMember2) == TRUE)

    {

        AssignCommand(oMember3, ClearAllActions());

        AssignCommand(oMember3, JumpToObject(oTarget));

    }

}



//::///////////////////////////////////////////////

//:: UT_JumpPartyToLocation

//:: Copyright (c) 2002 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Move the entire party to the location specified.

*/

//:://////////////////////////////////////////////

//:: Created By: John Winski

//:: Created On: Sept. 24, 2002

//:://////////////////////////////////////////////

void UT_JumpPartyToLocation(location lTarget)

{

    object oMember1 = GetPartyMemberByIndex(0);

    object oMember2 = GetPartyMemberByIndex(1);

    object oMember3 = GetPartyMemberByIndex(2);

    UT_RestorePartyToOneHealth();

    if (GetIsObjectValid(oMember1) == TRUE)

    {

        AssignCommand(oMember1, ClearAllActions());

        AssignCommand(oMember1, JumpToLocation(lTarget));

    }

    if (GetIsObjectValid(oMember2) == TRUE)

    {

        AssignCommand(oMember2, ClearAllActions());

        AssignCommand(oMember2, JumpToLocation(lTarget));

    }

    if (GetIsObjectValid(oMember2) == TRUE)

    {

        AssignCommand(oMember3, ClearAllActions());

        AssignCommand(oMember3, JumpToLocation(lTarget));

    }

}



//::///////////////////////////////////////////////

//:: Spawn Messenger

//:: Copyright (c) 2002 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Determines which messenger to spawn in for a specific planet.

    Uses the waypoint K_MESSENGER_SPAWN to determine where to place an incoming messenger



    Carth: KOR_DANEL == 1. Messenger = Jordo.

    Bastila: K_SWG_HELENA == 1. Messenger = Malare.

    Mission: Mis_MissionTalk == 5  Messenger = Lena

    Canderous: G_CAND_STATE == 8, G_CAND_PLOT == 0, K_CURRENT_PLANET != 35.  Messenger = Jagi

    Juhani: G_JUHANIH_STATE == 7, G_JUHANI_PLOT == 0. Messenger = Xor

    

    Endar Spire     5

    Taris           10

    Dantooine       15

    --Kashyyk       20

    --Manaan        25

    --Korriban      30

    --Tatooine      35

    Leviathan       40

    Unknown World   45

    Star Forge      50

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Sept 26, 2002

//:://////////////////////////////////////////////



void UT_SpawnMessenger()

{

    object oPC = GetFirstPC();

    object oWay = GetWaypointByTag("K_MESSENGER_SPAWN");

    object oNPC;

    int nGlobal_1, nGlobal_2;

    location lLocal;

    int bConditional = FALSE;

    int nXor = GetGlobalNumber("K_XOR_AMBUSH");



    //Do not fire any messenger plots on Kashyyyk if Chuundar is dead

    if(GetGlobalNumber("K_CURRENT_PLANET") == 20)

    {

        bConditional = GetGlobalBoolean("kas_ChuundarDead");

    }

    if(bConditional == FALSE)

    {

        if(nXor == 0 || nXor > 2)

        {

            if(GetIsObjectValid(oWay))

            {

                lLocal = GetLocation(oWay);

                //MODIFIED by Preston Watamaniuk on April 11

                //Added the exchange crony Ziagrom to tell the PC about the special store.

                if(GetGlobalNumber("K_KOTOR_MASTER") >= 20 &&

                   GetGlobalNumber("K_Exchange_Store") == 0 &&

                   GetGlobalBoolean("K_MESS_ZIAGROM") == FALSE)

                {

                    SetGlobalBoolean("K_MESS_ZIAGROM", TRUE);

                    oNPC = CreateObject(OBJECT_TYPE_CREATURE, "g_Ziagrom", lLocal);

                    NoClicksFor(2.2);

                    DelayCommand(2.0,  AssignCommand(oNPC, ActionStartConversation(oPC,"",FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE)));

                    return;

                }

                if(IsNPCPartyMember(NPC_BASTILA) &&

                   GetGlobalBoolean("K_MESS_BASTILA") == FALSE &&

                   GetGlobalNumber("K_CURRENT_PLANET") != 25 &&

                   GetGlobalNumber("K_SWG_HELENA") == 1)

                {

                        SetGlobalBoolean("K_MESSENGER_AVAILABLE", FALSE);

                        SetGlobalBoolean("K_MESS_BASTILA", TRUE);

                        oNPC = CreateObject(OBJECT_TYPE_CREATURE, "g_malare", lLocal);

                        NoClicksFor(2.2);

                        DelayCommand(2.0,  AssignCommand(oNPC, ActionStartConversation(oPC,"",FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE)));

                        //DelayCommand(2.0, UT_NPC_InitConversation(GetTag(oNPC)));

                        return;

                }

                if(IsNPCPartyMember(NPC_CARTH) &&

                   //MODIFIED by Preston Watamaniuk on May 13, 2003

                   //Added a check to make sure the Sith Acadamy is not closed before spawning in Jordo.

                   GetGlobalBoolean("KOR_END_HOSTILE") == FALSE &&

                   GetGlobalBoolean("K_MESS_CARTH") == FALSE &&

                   GetGlobalNumber("K_CURRENT_PLANET") != 30 &&

                   GetGlobalNumber("KOR_DANEL") == 1)

                {

                        SetGlobalBoolean("K_MESSENGER_AVAILABLE", FALSE);

                        SetGlobalBoolean("K_MESS_CARTH", TRUE);

                        oNPC = CreateObject(OBJECT_TYPE_CREATURE, "g_jordo", lLocal);

                        NoClicksFor(2.2);

                        DelayCommand(2.0,  AssignCommand(oNPC, ActionStartConversation(oPC,"",FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE)));

                        //DelayCommand(2.0, UT_NPC_InitConversation(GetTag(oNPC)));

                        return;

                }

                if(IsNPCPartyMember(NPC_JOLEE) &&

                   GetGlobalBoolean("K_MESS_JOLEE") == FALSE &&

                   GetGlobalNumber("K_CURRENT_PLANET") != 25 &&

                   GetGlobalNumber("K_CURRENT_PLANET") != 20 &&

                   GetGlobalNumber("MAN_MURDER_PLOT") == 0)

                {

                        SetGlobalBoolean("K_MESSENGER_AVAILABLE", FALSE);

                        SetGlobalBoolean("K_MESS_JOLEE", TRUE);

                        oNPC = CreateObject(OBJECT_TYPE_CREATURE, "g_davink", lLocal);

                        NoClicksFor(2.2);

                        DelayCommand(2.0,  AssignCommand(oNPC, ActionStartConversation(oPC,"",FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE)));

                        //DelayCommand(2.0, UT_NPC_InitConversation(GetTag(oNPC)));

                        return;

                }

                if(IsNPCPartyMember(NPC_JUHANI) &&

                   GetGlobalBoolean("K_MESS_JUHANI") == FALSE &&

                   (GetGlobalNumber("G_JUHANIH_STATE") > 5 && GetGlobalNumber("G_JUHANIP_STATE") < 10) &&

                   GetGlobalNumber("G_JUHANI_PLOT") == 0 &&

                   GetGlobalNumber("K_CURRENT_PLANET") != 15)

                {

                        //juhanih_state > 5, and juhanip_state < 10

                        SetGlobalBoolean("K_MESSENGER_AVAILABLE", FALSE);

                        SetGlobalBoolean("K_MESS_JUHANI", TRUE);

                        oNPC = CreateObject(OBJECT_TYPE_CREATURE, "g_xor", lLocal);

                        NoClicksFor(2.2);

                        DelayCommand(2.0,  AssignCommand(oNPC, ActionStartConversation(oPC,"",FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE)));

                        //DelayCommand(2.0, UT_NPC_InitConversation(GetTag(oNPC)));

                        return;

                }

                if(IsNPCPartyMember(NPC_CANDEROUS) &&

                   GetGlobalBoolean("K_MESS_CANDEROUS") == FALSE &&

                   GetGlobalNumber("K_CURRENT_PLANET") != 35 &&

                   GetGlobalNumber("G_CAND_STATE") >= 6 &&

                   GetGlobalBoolean("G_CAND_THING") == TRUE &&

                   GetGlobalNumber("G_CAND_PLOT") == 0)

                {

                        SetGlobalBoolean("K_MESSENGER_AVAILABLE", FALSE);

                        SetGlobalBoolean("K_MESS_CANDEROUS", TRUE);

                        oNPC = CreateObject(OBJECT_TYPE_CREATURE, "g_jagi", lLocal);

                        NoClicksFor(2.2);

                        DelayCommand(2.0,  AssignCommand(oNPC, ActionStartConversation(oPC,"",FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE)));

                        //DelayCommand(2.0, UT_NPC_InitConversation(GetTag(oNPC)));

                        return;

                }

                if(IsNPCPartyMember(NPC_MISSION) &&

                   GetGlobalBoolean("K_MESS_MISSION") == FALSE &&

                   GetGlobalNumber("K_CURRENT_PLANET") != 35 &&

                   GetGlobalNumber("K_CURRENT_PLANET") != 25 &&

                   GetGlobalNumber("Mis_MissionTalk") == 5)

                {

                        SetGlobalBoolean("K_MESSENGER_AVAILABLE", FALSE);

                        SetGlobalBoolean("K_MESS_MISSION", TRUE);

                        oNPC = CreateObject(OBJECT_TYPE_CREATURE, "g_lena", lLocal);

                        NoClicksFor(2.2);

                        DelayCommand(2.0,  AssignCommand(oNPC, ActionStartConversation(oPC,"",FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE)));

                        //DelayCommand(2.0, UT_NPC_InitConversation(GetTag(oNPC)));

                        return;

                }

            }

        }

    }

}



//::///////////////////////////////////////////////

//:: Exit Area

//:: Copyright (c) 2002 Bioware Corp.

//:://////////////////////////////////////////////

/*

    The NPC moves to an SW_EXIT waypoint and destroys

    itself.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Sept 27, 2002

//:://////////////////////////////////////////////

void UT_ExitArea(int nRun = FALSE)

{

    object oExit = GetWaypointByTag("SW_EXIT");

    object oExit2 = GetWaypointByTag("K_EXIT");



    if(GetIsObjectValid(oExit) && GetIsObjectValid(oExit2))

    {

        if(GetDistanceBetween(OBJECT_SELF, oExit) > GetDistanceBetween(OBJECT_SELF, oExit2))

        {

            oExit = oExit2;

        }

    }

    else if(GetIsObjectValid(oExit2) && !GetIsObjectValid(oExit))

    {

        oExit = oExit2;

    }



    ActionForceMoveToObject(oExit, nRun);

    ActionDoCommand(SetCommandable(TRUE));

    ActionDoCommand(DestroyObject(OBJECT_SELF));

    SetCommandable(FALSE);

}



//::///////////////////////////////////////////////

//:: UT_GetNumItems

//:: Copyright (c) 2002 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Counts the number of items with the given tag

    in the party inventory.

*/

//:://////////////////////////////////////////////

//:: Created By: John Winski

//:: Created On: October 15, 2002

//:://////////////////////////////////////////////

int UT_GetNumItems(object oTarget, string sItemTag)

{

    int nCount = 0;

    object oItem = GetFirstItemInInventory(oTarget);



    while (GetIsObjectValid(oItem) == TRUE)

    {

        if (GetTag(oItem) == sItemTag)

        {

            nCount = nCount + 1;

        }



        oItem = GetNextItemInInventory(oTarget);

    }



    return nCount;

}



//::///////////////////////////////////////////////

//:: Determines Item Cost

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns a value for how many parts or spikes

    a given dialogue option will cost.  The costs

    are as follows:

    Computer Use

    1.  Open all doors in area (cost: 3 spikes). The player can open all doors on the level.

    2.  Open all containers in area (cost: 3 spikes). The player can open all containers on the level.

    3.  Fill security room with gas (cost: 5 spikes).

    4.  Turn off all gun turrets (cost: 8 spikes).

    5.  Modify droid programming; target everything (cost: 10 spikes).

    6.  Deactivate all droids in area (cost: 8 spikes).



    Repair Use

    1.  Activate droid. Hostile to Sith faction. (cost: 3 repair unit)

    2.  Activate droid. Hostile to Sith faction. Enter patrol route. (cost: 5 repair unit)

    3.  Activate droid. Hostile to Sith faction. Hunter Killer mode. (cost: 7 repair unit)

    4.  Activate droid. Hostile to Sith faction. Follow mode. (cost: 5 repair unit)

*/

//:://////////////////////////////////////////////

//:: Created By: PReston Watamaniuk

//:: Created On: Nov 19, 2002

//:://////////////////////////////////////////////



int UT_DeterminesItemCost(int nDC, int nSkill)

{

        //AurPostString("DC " + IntToString(nDC), 5, 5, 3.0);

    float fModSkill =  IntToFloat(GetSkillRank(nSkill, GetPartyMemberByIndex(0)));

        //AurPostString("Skill Total " + IntToString(GetSkillRank(nSkill, GetPartyMemberByIndex(0))), 5, 6, 3.0);

    int nUse;

    fModSkill = fModSkill/4.0;

    nUse = nDC - FloatToInt(fModSkill);

        //AurPostString("nUse Raw " + IntToString(nUse), 5, 7, 3.0);

    if(nUse < 1)

    {

        //MODIFIED by Preston Watamaniuk, March 19

        //Put in a check so that those PC with a very high skill

        //could have a cost of 0 for doing computer work

        if(nUse <= -3)

        {

            nUse = 0;

        }

        else

        {

            nUse = 1;

        }

    }

        //AurPostString("nUse Final " + IntToString(nUse), 5, 8, 3.0);

    return nUse;

}



//::///////////////////////////////////////////////

//:: Remove X number of Computer Spikes

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Remove a number of computer spikes

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 19, 2002

//:://////////////////////////////////////////////

void UT_RemoveComputerSpikes(int nNumber)

{

    object oItem = GetItemPossessedBy(GetFirstPC(), "K_COMPUTER_SPIKE");

    if(GetIsObjectValid(oItem))

    {

        int nStackSize = GetItemStackSize(oItem);

        if(nNumber < nStackSize)

        {

            nNumber = nStackSize - nNumber;

            SetItemStackSize(oItem, nNumber);

        }

        else if(nNumber > nStackSize || nNumber == nStackSize)

        {

            DestroyObject(oItem);

        }

    }

}



//::///////////////////////////////////////////////

//:: Remove X number of Repair Parts

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Remove a number of repair parts

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 19, 2002

//:://////////////////////////////////////////////

void UT_RemoveRepairParts(int nNumber)

{

    object oItem = GetItemPossessedBy(GetFirstPC(), "K_REPAIR_PART");

    if(GetIsObjectValid(oItem))

    {

        int nStackSize = GetItemStackSize(oItem);

        if(nNumber < nStackSize)

        {

            nNumber = nStackSize - nNumber;

            SetItemStackSize(oItem, nNumber);

        }

        else if(nNumber > nStackSize || nNumber == nStackSize)

        {

            DestroyObject(oItem);

        }

    }

}



//::///////////////////////////////////////////////

//:: Return item amount

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Depending on the skill chosen, returns the

    number items relating to that skill

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 19, 2002

//:://////////////////////////////////////////////



int UT_ReturnSpikePartAmount(int nSkill)

{

    string sItem;

    int nCount = 0;

    if(nSkill == SKILL_COMPUTER_USE)

    {

        sItem = "K_COMPUTER_SPIKE";

    }

    else if(nSkill == SKILL_REPAIR)

    {

        sItem = "K_REPAIR_PART";

    }

    object oItem = GetItemPossessedBy(GetFirstPC(), sItem);

    if(GetIsObjectValid(oItem))

    {

        nCount = GetNumStackedItems(oItem);

    }

    return nCount;

}



//::///////////////////////////////////////////////

//:: Make Neutral

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Searches the area and changes all object with

    the specified tag to the neutral faction

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 20, 2002

//:://////////////////////////////////////////////

void UT_MakeNeutral(string sObjectTag)

{

    effect eStun = EffectDroidStun();

    int nCount = 1;

    object oDroid = GetNearestObjectByTag(sObjectTag);

    while(GetIsObjectValid(oDroid))

    {

        ApplyEffectToObject(DURATION_TYPE_PERMANENT, eStun, oDroid);

        nCount++;

        oDroid = GetNearestObjectByTag(sObjectTag, OBJECT_SELF, nCount);

    }

}



//::///////////////////////////////////////////////

//:: Make Insane

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Searches the area and changes all objects with

    the specified tag to the insane faction

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 20, 2002

//:://////////////////////////////////////////////

void UT_MakeInsane(string sObjectTag)

{

    int nCount = 1;

    object oDroid = GetNearestObjectByTag(sObjectTag);

    while(GetIsObjectValid(oDroid))

    {

        ChangeToStandardFaction(oDroid, STANDARD_FACTION_INSANE);

        UT_StartCombat(oDroid);



        nCount++;

        oDroid = GetNearestObjectByTag(sObjectTag, OBJECT_SELF, nCount);

    }

}



//::///////////////////////////////////////////////

//:: Stun Droids

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Searches the area and changes all objects with

    the specified tag to the insane faction

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 20, 2002

//:://////////////////////////////////////////////

void UT_StunDroids(string sObjectTag)

{

    effect eStun = EffectDroidStun();

    int nCount = 1;

    object oDroid = GetNearestObjectByTag(sObjectTag);

    while(GetIsObjectValid(oDroid))

    {

        ApplyEffectToObject(DURATION_TYPE_PERMANENT, eStun, oDroid);

        nCount++;

        oDroid = GetNearestObjectByTag(sObjectTag, OBJECT_SELF, nCount);

    }

}



//::///////////////////////////////////////////////

//:: Start a Fight

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Gets the nearest enemy that is seen and start combat

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 21, 2002

//:://////////////////////////////////////////////

void UT_StartCombat(object oObject)

{

    AssignCommand(oObject, ActionAttack(GetNearestCreature(CREATURE_TYPE_REPUTATION, REPUTATION_TYPE_ENEMY, oObject, 1, CREATURE_TYPE_PERCEPTION, PERCEPTION_SEEN)));

}



//::///////////////////////////////////////////////

//:: Gas a Rooom

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Releases gas into the room and kills all biologicals in the

    specified radius.  The radius should be between 2 - 5m

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 21, 2002

//:://////////////////////////////////////////////

void UT_GasRoom(string sWayTag, float fDistance, int bIndiscriminant = TRUE)

{

    object oWay = GetWaypointByTag(sWayTag);

    object oPC = GetFirstPC();

    if(GetIsObjectValid(oWay))

    {

        effect eVFX = EffectVisualEffect(3006);

        ApplyEffectAtLocation(DURATION_TYPE_INSTANT, eVFX, GetLocation(oWay));

        object oTarget = GetNearestCreature(CREATURE_TYPE_RACIAL_TYPE, RACIAL_TYPE_HUMAN, oWay, 1);

        int nCount = 1;

        while(GetIsObjectValid(oTarget) && GetDistanceBetween(oTarget, oWay) <= fDistance)

        {

            float fDelay = 3.0 + (IntToFloat(d10())/10.0);

            float fDelay2 = fDelay + 1.0 + (IntToFloat(d20())/10.0);



            if((GetIsFriend(oTarget, oPC) || GetIsNeutral(oTarget, oPC)) && bIndiscriminant == FALSE)

            {

                DelayCommand(fDelay, ApplyEffectToObject(DURATION_TYPE_TEMPORARY, EffectChoke(), oTarget, 3.0));

                DelayCommand(fDelay2, ApplyEffectToObject(DURATION_TYPE_PERMANENT, EffectPoison(POISON_ABILITY_SCORE_VIRULENT),oTarget));

            }

            else if(GetIsEnemy(oTarget, oPC) || bIndiscriminant == TRUE)

            {

                DelayCommand(fDelay, ApplyEffectToObject(DURATION_TYPE_TEMPORARY, EffectChoke(), oTarget, 10.0));

                DelayCommand(fDelay2, ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectDeath(), oTarget));

            }

            nCount++;

            oTarget = GetNearestCreature(CREATURE_TYPE_RACIAL_TYPE, RACIAL_TYPE_HUMAN, oWay, nCount);

        }

    }

}



//::///////////////////////////////////////////////

//:: Overload Conduit

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Overloads a power conduit and does 10d6 damage

    to all within the specified radius

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Nov 21, 2002

//:://////////////////////////////////////////////



void UT_OverloadConduit(string sObjectTag, float fDistance, int bIndiscriminant = TRUE)

{

    object oWay = GetObjectByTag(sObjectTag);

    if(GetIsObjectValid(oWay))

    {

        effect eFNF = EffectVisualEffect(VFX_FNF_GRENADE_ION);

        effect eVFXHit = EffectVisualEffect(1021);

        effect eVFXBeam = EffectBeam(VFX_BEAM_LIGHTNING_DARK_L, oWay, BODY_NODE_CHEST);

        effect eDam;



        object oTarget = GetNearestObject(OBJECT_TYPE_CREATURE, oWay, 1);

        int nCount = 1;

        int nDam = 1000;

        float fDelay = 0.3;



        AssignCommand(oWay, ActionPlayAnimation(ANIMATION_PLACEABLE_OPEN));



        DelayCommand(0.3, ApplyEffectAtLocation(DURATION_TYPE_INSTANT, eFNF, GetLocation(oWay)));

        while(GetIsObjectValid(oTarget) && GetDistanceBetween(oTarget, oWay) <= fDistance)

        {

            if(bIndiscriminant == TRUE || GetIsEnemy(oTarget, GetFirstPC()))

            {

                eDam = EffectDamage(nDam, DAMAGE_TYPE_ELECTRICAL);

                DelayCommand(fDelay, ApplyEffectToObject(DURATION_TYPE_INSTANT, eDam, oTarget));

                DelayCommand(fDelay, ApplyEffectToObject(DURATION_TYPE_TEMPORARY, eVFXBeam, oTarget, 1.0));

                DelayCommand(fDelay, ApplyEffectToObject(DURATION_TYPE_INSTANT, eVFXHit, oTarget, 1.0));

                fDelay = fDelay + 0.17;

            }

            nCount++;

            oTarget = GetNearestObject(OBJECT_TYPE_CREATURE, oWay, nCount);

        }

        ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectVisualEffect(VFX_PRO_DROID_KILL), oWay);



    }

}



///////////////////////////////////////////////////////////////////////////////

/*

    UT_ReturnToBase

    This function is used in the user defined event of a creature crossing a

    trigger used to pen in hostile creatures. When a creature crosses the

    trigger, it's actions are cleared, it is sent to the homebase waypoint and

    it is set non commanble. Once reaching its destination, it becomes

    commandable again. By defaut the standard tag for the waypoint is given, but

    a different one may be specified



    Created by Aidan Scanlan

    On Dec 2, 2002

*/

///////////////////////////////////////////////////////////////////////////////

void UT_ReturnToBase(string sTag = "wp_homebase")

{

    object oSelf = OBJECT_SELF;

    if(GetCommandable(oSelf))

    {

        ClearAllActions();

        CancelCombat(oSelf);

        ActionMoveToObject(GetNearestObjectByTag("wp_homebase"),TRUE,3.0f);

        ActionDoCommand( SetCommandable(TRUE,oSelf));

        SetCommandable(FALSE);

    }

}



//::///////////////////////////////////////////////

//:: UT_NPC_InitConversation

//:: Copyright (c) 2002 Bioware Corp.

//:://////////////////////////////////////////////

/*

    The specified NPC will start a conversation

    with the player.

*/

//:://////////////////////////////////////////////

//:: Created By: John Winski

//:: Created On: December 2, 2002

//:://////////////////////////////////////////////

void UT_NPC_InitConversation(string sNPCTag,string sDlg = "",object oEntered = OBJECT_INVALID)

{

    object oNPC = GetObjectByTag(sNPCTag);

    object oPC = GetFirstPC();

    UT_RestorePartyToOneHealth();

    // The NPC must exist.

    if (GetIsObjectValid(oNPC) == TRUE)

    {

        if (oPC == GetPartyMemberByIndex(0))

        {

            AssignCommand(oPC, ClearAllActions());

            AssignCommand(oNPC, ClearAllActions());

            CancelCombat(oPC);

            AssignCommand(oNPC, ActionStartConversation(oPC, sDlg, FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE));

        }

        else

        {

            // Fade to black, switch player control to the main character,

            // move the player to the NPC and start conversation.



            SetGlobalFadeOut();

            SetPartyLeader(NPC_PLAYER);



            object oParty1 = GetPartyMemberByIndex(1);

            object oParty2 = GetPartyMemberByIndex(2);

            

            //P.W. (June 7) - Put this in to terminate any player input during the fade.

            NoClicksFor(0.7);

            AssignCommand(oPC, ClearAllActions());

            AssignCommand(oNPC, ClearAllActions());

            CancelCombat(oPC);

            if (GetIsObjectValid(oEntered) == TRUE)

            {

                AssignCommand(oPC, DelayCommand(0.2, JumpToObject(oEntered)));

                AssignCommand(oPC, DelayCommand(0.4, SetFacingPoint(GetPosition(oNPC))));

            }

            else

            {

                AssignCommand(oPC, DelayCommand(0.2, JumpToObject(oNPC)));

            }

            AssignCommand(oParty1, DelayCommand(0.5, JumpToObject(oPC)));

            AssignCommand(oParty2, DelayCommand(0.5, JumpToObject(oPC)));

            AssignCommand(oNPC, ActionDoCommand(SetGlobalFadeIn(0.5, 2.0)));

            AssignCommand(oNPC, ActionStartConversation(oPC, sDlg, FALSE, CONVERSATION_TYPE_CINEMATIC, TRUE));

        }

    }

}



//::///////////////////////////////////////////////

//:: Set Starmap Journal

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Sets the Journal entry for the starmap

    automatically.



    Korriban - entry 10

    Tatooine - entry 20

    Kashyyyk - entry 30

    Manaan   - entry 40

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamanmiuk

//:: Created On: Dec 17, 2002

//:://////////////////////////////////////////////



void UT_SetStarmapJournal()

{

    string sModule = GetModuleFileName();

    if(sModule == "manm28ad") //Manaan

    {

        SetGlobalBoolean("K_STAR_MAP_MANAAN", TRUE);

        AddJournalQuestEntry("k_starforge", 40, TRUE);

    }

    else if(sModule == "korr_m39aa") //Korriban

    {

        SetGlobalBoolean("K_STAR_MAP_KORRIBAN", TRUE);

        AddJournalQuestEntry("k_starforge", 10, TRUE);

    }

    else if(sModule == "Kas_m25aa") //Kashyyyk

    {

        SetGlobalBoolean("K_STAR_MAP_KASHYYYK", TRUE);

        AddJournalQuestEntry("k_starforge", 30, TRUE);

    }

    else if(sModule == "Tat_m18ac") //Tatooine

    {

        SetGlobalBoolean("K_STAR_MAP_TATOOINE", TRUE);

        AddJournalQuestEntry("k_starforge", 20, TRUE);

    }

    if(GetGlobalNumber("K_STAR_MAP") == 50)

    {

        AddJournalQuestEntry("k_starforge", 50, TRUE);

    }

}



//::///////////////////////////////////////////////

//:: Spawn Creatures

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Creates number of creatures with a specific template at a specified waypoint tag.

    Total is the number times the loop will run.

    fTimeDelay is the number seconds between iterations.

    nSpawnIncrement is the number of templates spawned in per iteration.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamanmiuk

//:: Created On: Dec 17, 2002

//:://////////////////////////////////////////////

void UT_RunCombatEncounter(string sTemplate, string sTag, int nTotal = 3, float fTimeDelay = 1.5, int nSpawnIncrement = 1)

{

    if(fTimeDelay < 1.5)

    {

       fTimeDelay = 1.5;

    }

    object oWay = GetWaypointByTag(sTag);

    object oCreate;

    if(GetIsObjectValid(oWay))

    {

        int nCount = nSpawnIncrement;

        for(nCount; nCount != 0; nCount--)

        {

            oCreate = CreateObject(OBJECT_TYPE_CREATURE, sTemplate, GetLocation(oWay));

        }

        nTotal--;

        if(nTotal > 0)

        {

            DelayCommand(fTimeDelay, UT_RunCombatEncounter(sTemplate, sTag, nTotal, fTimeDelay, nSpawnIncrement));

        }

        fTimeDelay += fTimeDelay;

    }

}



//::///////////////////////////////////////////////

//:: Set Talk To Flag by Tag

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Loops through all object with a certain tag

    and sets their Talk To Flag to TRUE.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamanmiuk

//:: Created On: Dec 17, 2002

//:://////////////////////////////////////////////

void UT_SetTalkToFlagByTag(string sTag)

{

    int nCnt = 1;

    object oTrigger = GetNearestObjectByTag(sTag, GetFirstPC(), nCnt);

    while(GetIsObjectValid(oTrigger))

    {

        SetLocalBoolean(oTrigger, SW_PLOT_HAS_TALKED_TO, TRUE);

        nCnt++;

        oTrigger = GetNearestObjectByTag(sTag, GetFirstPC(), nCnt);

    }

}



//::///////////////////////////////////////////////

//:: Lock / Plot Twin Doors

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Loops through all doors with a certain tag

    and closes, locks and plots them.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamanmiuk

//:: Created On: Dec 17, 2002

//:://////////////////////////////////////////////

void UT_LockDoorDuplicates(string sTag)

{

    int nCount;

    object oDoor = GetNearestObjectByTag(sTag);

    while(GetIsObjectValid(oDoor) && GetObjectType(oDoor) == OBJECT_TYPE_DOOR)

    {

        if(oDoor != OBJECT_SELF)

        {

            AssignCommand(oDoor, ActionCloseDoor(oDoor));

            AssignCommand(oDoor, ActionLockObject(oDoor));

            AssignCommand(oDoor, SetPlotFlag(oDoor, TRUE));

        }

        nCount++;

        oDoor = GetNearestObjectByTag(sTag, OBJECT_SELF, nCount);

    }

}



//::///////////////////////////////////////////////

//:: Can Party Member Interject

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Check to see if the Party member specified is

    in the party and within the distance given.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jan 10, 2003

//:://////////////////////////////////////////////



int UT_CheckCanPartyMemberInterject(int nNPC_Constant, float fDistance)

{

    object oParty;



    if(IsNPCPartyMember(nNPC_Constant))

    {

        //MODIFIED by Preston Watamaniuk on April 24, 2003

        //Put this in so that NPCs who you turn down on a planet will not reinitiate on that planet again.

        int nPlanet = GetGlobalNumber("K_CURRENT_PLANET");

        string sConstant = "NPC_INIT_PLANET_";

        sConstant = "NPC_INIT_PLANET_" + IntToString(nNPC_Constant);

        int nConstant = GetGlobalNumber(sConstant);



        if(nNPC_Constant == NPC_BASTILA)

        {

            oParty = GetObjectByTag("Bastila");

        }

        else if(nNPC_Constant == NPC_CANDEROUS)

        {

            oParty = GetObjectByTag("Cand");

        }

        else if(nNPC_Constant == NPC_CARTH)

        {

            oParty = GetObjectByTag("Carth");

        }

        else if(nNPC_Constant == NPC_HK_47)

        {

            oParty = GetObjectByTag("HK47");

        }

        else if(nNPC_Constant == NPC_JOLEE)

        {

            oParty = GetObjectByTag("Jolee");

        }

        else if(nNPC_Constant == NPC_JUHANI)

        {

            oParty = GetObjectByTag("Juhani");

        }

        else if(nNPC_Constant == NPC_MISSION)

        {

            oParty = GetObjectByTag("Mission");

        }

        else if(nNPC_Constant == NPC_T3_M4)

        {

            oParty = GetObjectByTag("T3M4");

        }

        else if(nNPC_Constant == NPC_ZAALBAR)

        {

            oParty = GetObjectByTag("Zaalbar");

        }

        if(GetIsObjectValid(oParty) &&

           GetDistanceBetween(oParty, GetFirstPC()) <= fDistance &&

           nPlanet != nConstant)

        {

            return TRUE;

        }

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Reinitialize NPC Planet Constants

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This resets the variables for each party member

    that controls whether they will init on a

    particular planet.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 24, 2003

//:://////////////////////////////////////////////

void UT_ReinitializePartyPlanetVariables()

{

    string sConstant = "NPC_INIT_PLANET_";

    int nCnt = 0;



    for(nCnt; nCnt <= 8; nCnt++)

    {

        sConstant = "NPC_INIT_PLANET_" + IntToString(nCnt);

        SetGlobalNumber(sConstant, 0);

    }

}



//teleport party member

void UT_TeleportPartyMember(object oPartyMember, location lDest)

{



  if(!GetIsObjectValid(oPartyMember))

  {

    return;

  }

  if(GetCurrentHitPoints(oPartyMember) < 1)

  {

    ApplyEffectToObject(DURATION_TYPE_INSTANT,EffectResurrection(),oPartyMember);

    ApplyEffectToObject(DURATION_TYPE_INSTANT,EffectHeal(1),oPartyMember);

  }

  SetCommandable(TRUE,oPartyMember);

  AssignCommand(oPartyMember,ClearAllActions());

  AssignCommand(oPartyMember,ActionJumpToLocation(lDest));

}



//Returns true if oTarget is the object of interest of an attacker

int UT_GetUnderAttack(object oTarget)

{

  if(!GetIsObjectValid(oTarget))

  {

    return(FALSE);

  }



  object oAttacker = GetLastHostileActor(oTarget);

  return(GetIsObjectValid(oAttacker) || !GetIsDead(oAttacker) || GetObjectSeen(oAttacker, oTarget));

}



//:://////////////////////////////////////////////

/*

     This include handles jumping the party to the

     specified locations, good for controlling

     positions at the start of a cutscene.



     They will also be faced in the direction of

     the waypoints or objects they are being

     jumped to.

*/

//:://////////////////////////////////////////////

//:: Created By: Brad Prince

//:: Created On: Jan 23, 2003

//:://////////////////////////////////////////////

void UT_TeleportWholeParty(object oWP0, object oWP1, object oWP2)

{

   // The member the PC is in control of.

   object oMember0 = GetPartyMemberByIndex(0);

   // The second party member.

   object oMember1 = GetPartyMemberByIndex(1);

   // The third member.

   object oMember2 = GetPartyMemberByIndex(2);

   UT_RestorePartyToOneHealth();

   if(GetIsObjectValid(oMember0)) {

      UT_TeleportPartyMember(oMember0, GetLocation(oWP0));

      AssignCommand(oMember0, SetFacing(GetFacing(oWP0)));

   }

   if(GetIsObjectValid(oMember1)) {

      UT_TeleportPartyMember(oMember1, GetLocation(oWP1));

      DelayCommand(0.3, AssignCommand(oMember1, SetFacing(GetFacing(oWP1))));

   }

   if(GetIsObjectValid(oMember2)) {

      UT_TeleportPartyMember(oMember2, GetLocation(oWP2));

      DelayCommand(0.3, AssignCommand(oMember2, SetFacing(GetFacing(oWP2))));

   }

}



//::///////////////////////////////////////////////

//:: Action Pause Converation

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

     This will stop and start a conversation in 1

     step. Just pass the length of the pause.



     Be sure your commands will get carried out

     in the specified time and that the "pauser"

     is not killed.

*/

//:://////////////////////////////////////////////

//:: Created By: Brad Prince

//:: Created On: Jan 23, 2003

//:://////////////////////////////////////////////

void UT_ActionPauseConversation(float fDelay)

{

   ActionPauseConversation();

   DelayCommand(fDelay, ActionResumeConversation());

}



//::///////////////////////////////////////////////

//:: Spawn Available NPC

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Allows the uses to delay command on the creation

    of an NPC.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 5, 2003

//:://////////////////////////////////////////////



void UT_SpawnAvailableNPC(int nNPC, location lWay)

{

    object oNPC = SpawnAvailableNPC(nNPC, lWay);

}



//::///////////////////////////////////////////////

//:: Set Starmap Variables

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Advances K_STAR_MAP, sets the journal and

    sets the talk to flag.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 19, 2003

//:://////////////////////////////////////////////



void UT_StarMap1VariableSet()

{

    int nStar = GetGlobalNumber("K_STAR_MAP");

    int nBast = GetGlobalNumber("K_SWG_BASTILA");

    int nBool = GetLocalBoolean(OBJECT_SELF, SW_PLOT_HAS_TALKED_TO);



    if(nBool == FALSE)

    {

        //REMOVE THIS BEFORE SHIP

        AurPostString("v3.0 - K_STAR_MAP Before = " + IntToString(nStar), 5, 5, 5.0);



        nStar = nStar + 10;

        SetGlobalNumber("K_STAR_MAP",nStar);



        //REMOVE THIS BEFORE SHIP

        AurPostString("K_STAR_MAP After = " + IntToString(nStar), 5, 7, 5.0);



        if(nStar == 30)

        {

            if(nBast < 3)

            {

                SetGlobalNumber("K_SWG_BASTILA", 99);

            }

        }

        else if(nStar == 40)

        {

            //The player should now be captured by the Leviathan

            SetGlobalNumber("K_CAPTURED_LEV", 5);

            if(nBast < 5)

            {

                SetGlobalNumber("K_SWG_BASTILA", 99);

            }

        }

        else if(nStar == 50)

        {

            //The player should now have access to the unknown world.

            SetGlobalNumber("K_KOTOR_MASTER", 30);

        }

        SetLocalBoolean(OBJECT_SELF, SW_PLOT_HAS_TALKED_TO, TRUE);

        UT_SetStarmapJournal();

        AurPostString("Manaan Starmap = " + IntToString(GetGlobalBoolean("K_STAR_MAP_MANAAN")), 5, 9, 4.0);

        AurPostString("Kashyyyk Starmap = " + IntToString(GetGlobalBoolean("K_STAR_MAP_KASHYYYK")), 5, 11, 4.0);

        AurPostString("Korriban Starmap = " + IntToString(GetGlobalBoolean("K_STAR_MAP_KORRIBAN")), 5, 13, 4.0);

        AurPostString("Tatooine Starmap = " + IntToString(GetGlobalBoolean("K_STAR_MAP_TATOOINE")), 5, 15, 4.0);

    }

}



//::///////////////////////////////////////////////

//:: Play Starmap Animations

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Plays the animations necessary for the current

    state of the starmap variable

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 19, 2003

//:://////////////////////////////////////////////

void UT_StarMap2PlayAnimation()

{

    int nStar = GetGlobalNumber("K_STAR_MAP");

    int nBool = GetLocalBoolean(OBJECT_SELF, SW_PLOT_HAS_TALKED_TO);

    float fDelay = 30.0;

    if(nBool == FALSE)

    {

        ActionPlayAnimation(ANIMATION_PLACEABLE_ACTIVATE);

        ActionPlayAnimation(UT_StarMap3GetLoopAnim(nStar));

        if(nStar == 40)//This variable is the pre-activation value.  It is going from 40 to 50

        {

            fDelay = 60.0;

        }

        DelayCommand(fDelay, ActionPlayAnimation(ANIMATION_PLACEABLE_DEACTIVATE));

    }

}



//::///////////////////////////////////////////////

//:: Returns the Appropriate Starmap Anim Loop

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns the appropriate animation loop for the

    Star Map based on the value used before the

    new variable is set.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 19, 2003

//:://////////////////////////////////////////////

int UT_StarMap3GetLoopAnim(int nStarMapVar)

{

    if(nStarMapVar == 0)

    {

        return ANIMATION_PLACEABLE_ANIMLOOP01;

    }

    else if(nStarMapVar == 10)

    {

        return ANIMATION_PLACEABLE_ANIMLOOP02;

    }

    else if(nStarMapVar == 20)

    {

        return ANIMATION_PLACEABLE_ANIMLOOP03;

    }

    else if(nStarMapVar == 30)

    {

        return ANIMATION_PLACEABLE_ANIMLOOP04;

    }

    else if(nStarMapVar == 40)

    {

        return ANIMATION_PLACEABLE_ANIMLOOP06;

    }



    return -1;

}



//::///////////////////////////////////////////////

//:: Generic Starmap Handler

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Runs the entire Starmap sequence as a black

    box with no extra scripting required.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 19, 2003

//:://////////////////////////////////////////////

void UT_StarMap4RunStarMap()

{

    UT_StarMap2PlayAnimation();

    UT_StarMap1VariableSet();

}



//////////////////////////////////////////////////////////////////////

/*    This function removes party members. It stores the npc constants

    of the removed party members.



    Aidan-Feb 20,03

*/

//////////////////////////////////////////////////////////////////////

void UT_StoreParty()

{

    if(GetPartyMemberByIndex(0) != GetFirstPC())

    {

        SetPartyLeader(NPC_PLAYER);

    }

    object oNPC1 = GetPartyMemberByIndex(1);

    object oNPC2 = GetPartyMemberByIndex(2);





    int nIdx, bFound1, bFound2, bRemove;

    for (nIdx = NPC_BASTILA; nIdx <= NPC_ZAALBAR && !bFound2; nIdx++)

    {

        bRemove = IsNPCPartyMember(nIdx);

        if(bRemove)

        {

            if(bFound1 == FALSE)

            {

                RemovePartyMember(nIdx);

                SetGlobalNumber("K_PARTY_STORE1",nIdx);

                bFound1 = TRUE;

                SetGlobalBoolean("K_PARTY_STORED",TRUE);

            }

            else

            {

                RemovePartyMember(nIdx);

                SetGlobalNumber("K_PARTY_STORE2",nIdx);

                bFound2 = TRUE;

                SetGlobalBoolean("K_PARTY_STORED",TRUE);

            }

        }





        bRemove = FALSE;

    }

    if(GetIsObjectValid(oNPC1))

    {

        DestroyObject(oNPC1);

    }

    if(GetIsObjectValid(oNPC2))

    {

        DestroyObject(oNPC2);

    }



}



//::///////////////////////////////////////////////

//:: Restore NPC

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

    This function restore party members. It will only

    restore party members removed via the

    UT_StoreParty function

*/

//:://////////////////////////////////////////////

//:: Created By: Aidan Scanlan

//:: Created On: Feb 20, 2003

//:://////////////////////////////////////////////

void UT_RestoreParty()

{

    int nNPC1 = GetGlobalNumber("K_PARTY_STORE1");

    int nNPC2 = GetGlobalNumber("K_PARTY_STORE2");

    object oNPC;

    if(GetGlobalBoolean("K_PARTY_STORED"))

    {

        if(nNPC1 >= NPC_BASTILA && nNPC1 <= NPC_ZAALBAR)

        {

            if(GetIsObjectValid(GetPartyMemberByIndex(1)) == FALSE)

            {

                oNPC = SpawnAvailableNPC(nNPC1,GetLocation(GetFirstPC()));

                if(GetIsObjectValid(oNPC))

                {

                    AddPartyMember(nNPC1,oNPC);

                }

            }

        }

        if(nNPC2 >= NPC_BASTILA && nNPC2 <= NPC_ZAALBAR)

        {

            if(GetIsObjectValid(GetPartyMemberByIndex(2)) == FALSE)

            {

                oNPC = SpawnAvailableNPC(nNPC2,GetLocation(GetFirstPC()));

                if(GetIsObjectValid(oNPC))

                {

                    AddPartyMember(nNPC2,oNPC);

                }

            }



        }

    }

    SetGlobalNumber("K_PARTY_STORE2",-2);

    SetGlobalNumber("K_PARTY_STORE1",-2);

    SetGlobalBoolean("K_PARTY_STORED",FALSE);

}



//::///////////////////////////////////////////////

//:: Return NPC Integer

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Returns the NPC code for the given object if

    it is a NPC, otherwise it returns -1

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: Feb 26, 2003

//:://////////////////////////////////////////////



int UT_GetNPCCode(object oNPC)

{

  string sTag = GetTag(oNPC);



  if(!GetIsObjectValid(oNPC))

  {

    return(-1);

  }



  if(sTag == "bastila")

  {

    return(NPC_BASTILA);

  }



  if(sTag == "cand")

  {

    return(NPC_CANDEROUS);

  }



  if(sTag == "carth")

  {

    return(NPC_CARTH);

  }



  if(sTag == "hk47")

  {

    return(NPC_HK_47);

  }



  if(sTag == "jolee")

  {

    return(NPC_JOLEE);

  }



  if(sTag == "juhani")

  {

    return(NPC_JUHANI);

  }



  if(sTag == "mission")

  {

    return(NPC_MISSION);

  }



  if(sTag == "t3m4")

  {

    return(NPC_T3_M4);

  }



  if(sTag == "zaalbar")

  {

    return(NPC_ZAALBAR);

  }



  return(-1);

}



//::///////////////////////////////////////////////

//:: Restore Party Member to 1 Vitality

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Restores all party mambers to 1 hp if

    tempoarily dead

*/

//:://////////////////////////////////////////////

//:: Created By: Aidan Scanlan

//:: Created On: March 1, 2003

//:://////////////////////////////////////////////



void UT_RestorePartyToOneHealth()

{

    int nIdx = 0;

    object oParty = GetPartyMemberByIndex(nIdx);

    while (GetIsObjectValid(oParty))

    {

        if(GetCurrentHitPoints(oParty) < 1)

        {

            ApplyEffectToObject(DURATION_TYPE_INSTANT,EffectResurrection(),oParty);

            ApplyEffectToObject(DURATION_TYPE_INSTANT,EffectHeal(1),oParty);

        }

        nIdx++;

        oParty = GetPartyMemberByIndex(nIdx);

    }

}



//::///////////////////////////////////////////////

//:: Heal Party

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Cycles throught the entire party and heals

    them.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 28, 2003

//:://////////////////////////////////////////////



void UT_HealParty()

{

    object oParty;

    int nCnt = 0;

    for(nCnt; nCnt < 3; nCnt++)

    {

        oParty = GetPartyMemberByIndex(nCnt);

        if(GetIsObjectValid(oParty))

        {

            ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectHeal(500), oParty);

            ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectHealForcePoints(500), oParty);

        }

    }

}



//::///////////////////////////////////////////////

//:: Heal Party Member

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Heals a single target to full.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Feb 28, 2003

//:://////////////////////////////////////////////

void UT_HealNPC(object oNPC)

{

    ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectHeal(500), oNPC);

    ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectHealForcePoints(500), oNPC);

}



//::///////////////////////////////////////////////

//:: Alter Stack

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Alters the stack of a given object by the

    specified amount. If the stack is only 1 then

    the object is destroyed.

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: March 3, 2003

//:://////////////////////////////////////////////

void UT_AlterItemStack(object oItem,int iNum = 1,int bDecrement = TRUE)

{

    int iStackSize;



    if(!GetIsObjectValid(oItem) || iNum == 0)

    {

        return;

    }



    if(bDecrement)

    {

        iNum = -iNum;

    }



    iStackSize = GetItemStackSize(oItem);

    if(iNum > 0)

    {

        SetItemStackSize(oItem,iStackSize+iNum);

    }

    else

    {

        if(iStackSize+iNum <= 0)

        {

          //MODIFIED by Preston Watamaniuk on May 13, 2003

          //Added the command below to set the stack to 1 before destroying it.

          SetItemStackSize(oItem,1);

          DestroyObject(oItem,0.0,TRUE);

        }

        else

        {

          SetItemStackSize(oItem,iStackSize+iNum);

        }

    }

}



//::///////////////////////////////////////////////

//:: Heal All Party NPCs

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Searches through the area and heals all of the

    party members who are there. Used on the Ebon

    Hawk and the Taris Apartment.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: March 5, 2003

//:://////////////////////////////////////////////



void UT_HealAllPartyNPCs()

{

    object oNPC1 = GetObjectByTag("bastila");

    object oNPC2 =  GetObjectByTag("carth");

    object oNPC3 = GetObjectByTag("cand");

    object oNPC4 = GetObjectByTag("hk47");

    object oNPC5 = GetObjectByTag("jolee");

    object oNPC6 = GetObjectByTag("juhani");

    object oNPC7 = GetObjectByTag("mission");

    object oNPC8 = GetObjectByTag("t3m4");

    object oNPC9 = GetObjectByTag("zaalbar");

    object oCurrent;



    int nCnt = 1;

    while(nCnt <= 9)

    {

        if(nCnt == 1){oCurrent = oNPC1;}

        if(nCnt == 2){oCurrent = oNPC2;}

        if(nCnt == 3){oCurrent = oNPC3;}

        if(nCnt == 4){oCurrent = oNPC4;}

        if(nCnt == 5){oCurrent = oNPC5;}

        if(nCnt == 6){oCurrent = oNPC6;}

        if(nCnt == 7){oCurrent = oNPC7;}

        if(nCnt == 8){oCurrent = oNPC8;}

        if(nCnt == 9){oCurrent = oNPC9;}



        if(GetIsObjectValid(oCurrent))

        {

            UT_HealNPC(oCurrent);

        }

        nCnt++;

    }

    UT_HealNPC(GetFirstPC());

}



//::///////////////////////////////////////////////

//:: Clear Party Members

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Goes through the party and removes them.

    This is best used on Module Load when the

    object are not actually created yet.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: March 6, 2003

//:://////////////////////////////////////////////

void UT_ClearAllPartyMembers()

{

    int nCnt;

    for(nCnt; nCnt <= 8; nCnt++)

    {

        if(IsNPCPartyMember(nCnt))

        {

            RemovePartyMember(nCnt);

        }

    }

}



//::///////////////////////////////////////////////

//:: DC check using an ability score only

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Does a DC check just using an ability score

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: March 13, 2003

//:://////////////////////////////////////////////

int UT_AbilityCheck(int iDC, int iAbility, object oTarget)

{

    if(!GetIsObjectValid(oTarget))

    {

        return(FALSE);

    }



    if(GetAbilityScore(oTarget,iAbility) + (Random(20)+1) >= iDC)

    {

        return(TRUE);

    }

    else

    {

        return(FALSE);

    }

}



//::///////////////////////////////////////////////

//:: Make Neutral2

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Searches the area and changes all objects with

    the specified tag to the neutral faction

*/

//:://////////////////////////////////////////////

//:: Created By: Peter T.

//:: Created On: March 17, 2003

//:://////////////////////////////////////////////

void UT_MakeNeutral2(string sObjectTag)

{

    int nCount = 1;



    // get first object

    object oObject = GetNearestObjectByTag(sObjectTag);



    while(GetIsObjectValid(oObject))

    {

        // set to Neutral

        ChangeToStandardFaction(oObject, STANDARD_FACTION_NEUTRAL);



        // get next object

        nCount++;

        oObject = GetNearestObjectByTag(sObjectTag, OBJECT_SELF, nCount);

    }

}



//::///////////////////////////////////////////////

//:: Make Hostile1

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Searches the area and changes all objects with

    the specified tag to the Hostile_1 faction

*/

//:://////////////////////////////////////////////

//:: Created By: Peter T.

//:: Created On: March 17, 2003

//:://////////////////////////////////////////////

void UT_MakeHostile1(string sObjectTag)

{

    int nCount = 1;



    // get first object

    object oObject = GetNearestObjectByTag(sObjectTag);



    while(GetIsObjectValid(oObject))

    {

        // set to Hostile_1

        ChangeToStandardFaction(oObject, STANDARD_FACTION_HOSTILE_1);



        // get next object

        nCount++;

        oObject = GetNearestObjectByTag(sObjectTag, OBJECT_SELF, nCount);

    }

}



//::///////////////////////////////////////////////

//:: Make Friendly1

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Searches the area and changes all objects with

    the specified tag to the Friendly_1 faction

*/

//:://////////////////////////////////////////////

//:: Created By: Peter T.

//:: Created On: March 17, 2003

//:://////////////////////////////////////////////

void UT_MakeFriendly1(string sObjectTag)

{

    int nCount = 1;



    // get first object

    object oObject = GetNearestObjectByTag(sObjectTag);



    while(GetIsObjectValid(oObject))

    {

        // set to Friendly_1

        ChangeToStandardFaction(oObject, STANDARD_FACTION_FRIENDLY_1);



        // get next object

        nCount++;

        oObject = GetNearestObjectByTag(sObjectTag, OBJECT_SELF, nCount);

    }

}



//::///////////////////////////////////////////////

//:: Make Friendly2

//:: Copyright (c) 2003 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Searches the area and changes all objects with

    the specified tag to the Friendly_2 faction

*/

//:://////////////////////////////////////////////

//:: Created By: Peter T.

//:: Created On: March 17, 2003

//:://////////////////////////////////////////////

void UT_MakeFriendly2(string sObjectTag)

{

    int nCount = 1;



    // get first object

    object oObject = GetNearestObjectByTag(sObjectTag);



    while(GetIsObjectValid(oObject))

    {

        // set to Friendly_2

        ChangeToStandardFaction(oObject, STANDARD_FACTION_FRIENDLY_2);



        // get next object

        nCount++;

        oObject = GetNearestObjectByTag(sObjectTag, OBJECT_SELF, nCount);

    }

}



//::///////////////////////////////////////////////

//:: UT_ActivateTortureCage

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    performs a standard torture cage effect

*/

//:://////////////////////////////////////////////

//:: Created By: Jason Booth

//:: Created On: April 1, 2003

//:://////////////////////////////////////////////

void DoTortureAnims(float fDuration)

{

    ActionPlayAnimation(ANIMATION_LOOPING_SPASM,1.0,fDuration/3.0);

    ActionPlayAnimation(ANIMATION_LOOPING_HORROR,1.0,fDuration/3.0);

    ActionPlayAnimation(ANIMATION_LOOPING_SPASM,1.0,fDuration/3.0);

}

void UT_ActivateTortureCage(object oCage, object oTarget,float fDuration)

{

    //AssignCommand(oCage,

    //ActionPlayAnimation(ANIMATION_PLACEABLE_ACTIVATE));

    //ApplyEffectToObject(DURATION_TYPE_TEMPORARY,EffectHorrified(),oTarget,fDuration);

    AssignCommand(oTarget,DoTortureAnims(fDuration));

    ApplyEffectToObject(DURATION_TYPE_TEMPORARY,EffectBeam(VFX_BEAM_LIGHTNING_DARK_S, oCage, BODY_NODE_HEAD),oTarget,fDuration);

    //DelayCommand(fDuration,AssignCommand(oCage,ActionPlayAnimation(ANIMATION_PLACEABLE_DEACTIVATE)));

}



//::///////////////////////////////////////////////

//:: Validate Jump

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    If the first three letters of the last module

    do not match the first three letters of the

    space port then function will return false.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 15, 2003

//:://////////////////////////////////////////////

int UT_ValidateJump(string sLastModule)

{

    int nJump = FALSE;



    string sCurrentModule = GetModuleFileName();

    PrintString("JUMP VALIDATION: CURRENT = " + sCurrentModule + " LAST = " + sLastModule);

    PrintString("JUMP VALIDATION: SUBSTRING: " + GetSubString(sCurrentModule, 0,3) + " = " + GetSubString(sLastModule, 0,3));

    if(GetSubString(sCurrentModule, 0,3) == GetSubString(sLastModule, 0,3))

    {

        nJump = TRUE;

    }

    else if(sCurrentModule != "ebo_m12aa")

    {

        SetGlobalString("K_LAST_MODULE", "NO_MODULE");

    }

    return nJump;

}



//::///////////////////////////////////////////////

//:: Play On Click Reaction

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Makes the animal face the PC, do its victory

    and play a sound passed in. Should be used

    in conjunction with the k_def_interact spawn in

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: May 31, 2003

//:://////////////////////////////////////////////



void UT_DoAmbientReaction(string sSound)

{

    //ActionDoCommand(SetLocalBoolean(OBJECT_SELF, 72, FALSE));

    PlaySound(sSound);

    SetFacingPoint(GetPosition(GetPCSpeaker()));

    ActionPlayAnimation(ANIMATION_FIREFORGET_VICTORY1);

    //DelayCommand(2.0, ActionDoCommand(SetLocalBoolean(OBJECT_SELF, 72, TRUE)));

}

''',

    'k_inc_walkways': b'''//:: k_inc_walkways

/*

    v1.0

    Walk Way Points Include

    used by k_inc_generic

    

    NOTE - To get these functions

    use k_inc_generic

*/

//:: Created By: Preston Watamaniuk

//:: Copyright (c) 2002 Bioware Corp.



int WALKWAYS_CURRENT_POSITION = 0;

int WALKWAYS_END_POINT = 1;

int WALKWAYS_SERIES_NUMBER = 2;



int	SW_FLAG_AMBIENT_ANIMATIONS	=	29;

int	SW_FLAG_AMBIENT_ANIMATIONS_MOBILE =	30;

int	SW_FLAG_WAYPOINT_WALK_ONCE	=	34;

int	SW_FLAG_WAYPOINT_WALK_CIRCULAR	=	35;

int	SW_FLAG_WAYPOINT_WALK_PATH	=	36;

int	SW_FLAG_WAYPOINT_WALK_STOP	=	37; //One to three

int	SW_FLAG_WAYPOINT_WALK_RANDOM	=	38;

int SW_FLAG_WAYPOINT_WALK_RUN    =   39;

int SW_FLAG_WAYPOINT_DIRECTION = 41;

int SW_FLAG_WAYPOINT_DEACTIVATE = 42;

int SW_FLAG_WAYPOINT_WALK_STOP_LONG = 46;

int SW_FLAG_WAYPOINT_WALK_STOP_RANDOM = 47;



//Makes OBJECT_SELF walk way points based on the spawn in conditions set out.

void GN_WalkWayPoints();

//Sets the series number from 01 to 99 on a creature so that the series number and not the creature's tag is used for walkway points

void GN_SetWalkWayPointsSeries(int nSeriesNumber);

//Sets Generic Spawn In Conditions

void GN_SetSpawnInCondition(int nFlag, int nState = TRUE);

//Gets the boolean state of a generic spawn in condition.

int GN_GetSpawnInCondition(int nFlag);

//Moves an object to the last waypoint in a series

void GN_MoveToLastWayPoint(object oToMove);

//Moves an object to a random point in the series

void GN_MoveToRandomWayPoint(object oToMove);

//Moves an object to a sepcific point in the series

void GN_MoveToSpecificWayPoint(object oToMove, int nArrayNumber);

//Determines the correct direction to proceed in a walkway points array.

int GN_GetWayPointDirection(int nEndArray, int nCurrentPosition);

//Should only be called from within SetListendingPatterns

void GN_SetUpWayPoints();

//Play an animation between way points.

void GN_PlayWalkWaysAnimation();

//Inserts a print string into the log file for debugging purposes for the walkways include.

void WK_MyPrintString(string sString);

//Are valid walkway points available

int GN_CheckWalkWays(object oTarget);



//::///////////////////////////////////////////////

//:: Walk Way Points

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Makes OBJECT_SELF walk way points based on a

    number of spawn in conditions.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: July 15, 2002

//:://////////////////////////////////////////////



void GN_WalkWayPoints()

{

    if(!GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_DEACTIVATE))

    {

        string sPost = "POST_";

        string sWays = "WP_";

        string sWayNumber;



        int nCurrentTarget = GetLocalNumber(OBJECT_SELF, WALKWAYS_CURRENT_POSITION);

        int nEndArray = GetLocalNumber(OBJECT_SELF, WALKWAYS_END_POINT);

        int nSeriesInt = GetLocalNumber(OBJECT_SELF, WALKWAYS_SERIES_NUMBER);

        //Used where you want the creature to use a numbered series instead of their own tag.



        if(nCurrentTarget < 10 &&  nCurrentTarget > 0)

        {

            sWayNumber = "0" + IntToString(nCurrentTarget);

        }

        else if(nCurrentTarget == 0)

        {

            //August 2, 2002 - Jason Booth - changed to randomize start wp

            if(GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_WALK_RANDOM))

            {

                nCurrentTarget = Random(nEndArray) + 1;

                if(nCurrentTarget < 10)

                {

                  sWayNumber = "0" + IntToString(nCurrentTarget);

                }

                else

                {

                  sWayNumber = IntToString(nCurrentTarget);

                }

            }

            else

            {

              sWayNumber = "01";

            }

        }

        else if(nCurrentTarget < 10)

        {

            sWayNumber = "0" + IntToString(nCurrentTarget);

        }

        else

        {

            sWayNumber = IntToString(nCurrentTarget);

        }



        string sMoveWay;

        string sTestWay;

        //Test to see if the series waypoints are being used and if so then build sTestWay with the number not tag.

        if(nSeriesInt > 0)

        {

            string sSeriesWay;

            if(nSeriesInt < 10)

            {

                sSeriesWay = "0" + IntToString(nSeriesInt);

            }

            else

            {

                sSeriesWay = IntToString(nSeriesInt);

            }

            sTestWay = sWays + sSeriesWay + "_02";

        }

        //Use object tag if there is no series number

        else

        {

            sTestWay = sWays + GetTag(OBJECT_SELF) + "_02";

        }



        object oTestWay = GetWaypointByTag(sTestWay);



        if(nEndArray == 0 && GetIsObjectValid(oTestWay))

        {

            //GN_PostString("SET LISTENING PATTERNS HAS NOT RUN PLEASE USE IN SPAWN IN SCRIPT");

        }



        if(GetIsObjectValid(oTestWay))

        {

            int nLength = GetStringLength(sTestWay);

            sMoveWay = GetStringLeft(sTestWay, nLength - 2) + sWayNumber;

            //sWays + GetTag(OBJECT_SELF) + "_" + sWayNumber;

        }

        else

        {

            sWays = "UNKNOWN";

            sMoveWay = sPost + GetTag(OBJECT_SELF);

        }



        object oWay = GetWaypointByTag(sMoveWay);

        int nRun = GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_WALK_RUN);



        //Check if the target waypoint is close enough to warrent moving on to the next waypoint.

        if(GetDistanceToObject2D(oWay) <= 2.5)

        {

            int nDirection;

            if(GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_WALK_RANDOM))

            {

                nCurrentTarget = Random(nEndArray) + 1;

            }

            else if(nCurrentTarget < nEndArray && !GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_WALK_RANDOM))

            {

                nDirection = GN_GetWayPointDirection(nEndArray, nCurrentTarget);

                nCurrentTarget = nCurrentTarget + nDirection;

            }

            else if(nCurrentTarget == nEndArray)

            {

                nDirection = GN_GetWayPointDirection(nEndArray, nCurrentTarget);

                if(GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_WALK_ONCE))

                {

                    GN_SetSpawnInCondition(SW_FLAG_WAYPOINT_DEACTIVATE);

                }

                else if(GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_WALK_CIRCULAR))

                {

                    nCurrentTarget = 1;

                    GN_SetSpawnInCondition(SW_FLAG_WAYPOINT_DIRECTION, FALSE);

                }

                else

                {

                    nCurrentTarget = nCurrentTarget + nDirection;

                }

            }

        }



        if(GetIsObjectValid(GetWaypointByTag(sMoveWay)))

        {

            //MODIFIED by Preston Watamaniuk on March 13

            //Took out the clear all actions. It was mucking up the chain of commands.

            //ActionDoCommand(ClearAllActions());

            

            int nRand;

            if(GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_WALK_STOP))

            {

                nRand = d3();

            }

            else if(GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_WALK_STOP_LONG))

            {

                nRand = d6()+6;

            }

            else if(GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_WALK_STOP_RANDOM))

            {

                nRand = d12();

            }

            else if(nRand > 0)

            {

                ActionWait(IntToFloat(nRand)); //ACTION

            }

            oWay = GetWaypointByTag(sMoveWay);

            //Calculate the timeout based on the distance that needs to be traveled.

            float fTimeOut = GetDistanceBetween2D(GetWaypointByTag(sMoveWay), OBJECT_SELF)/1.25;

            if(fTimeOut < 30.0)

            {

                fTimeOut = 30.0;

            }

            //WK_MyPrintString("WALKWAYS DEBUG *************** Adding Action: Force Move");

            ActionForceMoveToObject(oWay, GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_WALK_RUN), 2.5, fTimeOut); //ACTION



            //MODIFIED by Preston Watamaniuk on March 13

            //Added this piece of code to add ambient animations to Walkways.

            if(GN_GetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS))

            {

                //WK_MyPrintString("WALKWAYS DEBUG *************** Adding Action: Animation");

                ActionDoCommand(GN_PlayWalkWaysAnimation()); //ACTION

            }

            SetLocalNumber(OBJECT_SELF, WALKWAYS_CURRENT_POSITION, nCurrentTarget);

            if(sWays != "UNKNOWN")

            {

                //WK_MyPrintString("WALKWAYS DEBUG *************** Adding Action: Walkways Interate");

                ActionDoCommand(GN_WalkWayPoints());   //ACTION

            }

        }

    }

}



void GN_SetWalkWayPointsSeries(int nSeriesNumber)

{

    SetLocalNumber(OBJECT_SELF, WALKWAYS_SERIES_NUMBER, nSeriesNumber);

}



//::///////////////////////////////////////////////

//:: Set Spawn In Condition

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Sets the Generic Spawn In Conditions

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: July 15, 2002

//:://////////////////////////////////////////////

void GN_SetSpawnInCondition(int nFlag, int nState = TRUE)

{

    //WK_MyPrintString("GENERIC DEBUG *************** Setting Local Number (" + IntToString(nFlag) + ") = " + IntToString(nState));

    SetLocalBoolean(OBJECT_SELF, nFlag, nState);

}



//::///////////////////////////////////////////////

//:: Get Spawn In Condition

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Gets the Generic Spawn In Conditions

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: July 15, 2002

//:://////////////////////////////////////////////

int GN_GetSpawnInCondition(int nFlag)

{

    int nLocal = GetLocalBoolean(OBJECT_SELF, nFlag);

    if(nLocal > 0)

    {

        return TRUE;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Preston Watamaniuk

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Moves the passed in object to the last waypoint

    in that NPCs series of waypoints.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Aug 12, 2002

//:://////////////////////////////////////////////



void GN_MoveToLastWayPoint(object oToMove)

{

    int nLastWay = GetLocalNumber(oToMove, WALKWAYS_END_POINT);

    int nSeries = GetLocalNumber(oToMove, WALKWAYS_SERIES_NUMBER);

    string sString;

    if(nSeries > 0)

    {

        string sSeriesWay;

        if(nSeries < 10)

        {

            sSeriesWay = "0" + IntToString(nSeries);

        }

        else

        {

            sSeriesWay = IntToString(nSeries);

        }

        sString = "WP_" + sSeriesWay;

    }

    else

    {

        sString = "WP_" + GetTag(oToMove);

    }

    if(nLastWay < 10)

    {

        sString = sString + "_0" + IntToString(nLastWay);

    }

    else

    {

        sString = sString + "_" + IntToString(nLastWay);

    }



    object oWay = GetWaypointByTag(sString);

    if(GetIsObjectValid(oWay))

    {

        AssignCommand(oToMove, ClearAllActions());

        AssignCommand(oToMove, ActionMoveToObject(oWay, FALSE));

    }

}



//::///////////////////////////////////////////////

//:: Preston Watamaniuk

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Moves the passed in object to a random waypoint

    in that NPCs series of waypoints.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Aug 12, 2002

//:://////////////////////////////////////////////



void GN_MoveToRandomWayPoint(object oToMove)

{

    int nLastWay = GetLocalNumber(oToMove, WALKWAYS_END_POINT);

    int nRandom = Random(nLastWay)+1;

    int nSeries = GetLocalNumber(oToMove, WALKWAYS_SERIES_NUMBER);

    string sString;

    if(nSeries > 0)

    {

        string sSeriesWay;

        if(nSeries < 10)

        {

            sSeriesWay = "0" + IntToString(nSeries);

        }

        else

        {

            sSeriesWay = IntToString(nSeries);

        }

        sString = "WP_" + sSeriesWay;

    }

    else

    {

        sString = "WP_" + GetTag(oToMove);

    }

    if(nLastWay < 10)

    {

        sString = sString + "_0" + IntToString(nRandom);

    }

    else

    {

        sString = sString + "_" + IntToString(nRandom);

    }



    object oWay = GetWaypointByTag(sString);

    if(GetIsObjectValid(oWay))

    {

        AssignCommand(oToMove, ClearAllActions());

        AssignCommand(oToMove, ActionMoveToObject(oWay, FALSE));

    }

}



//::///////////////////////////////////////////////

//:: Preston Watamaniuk

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Moves the passed in object to a specified waypoint

    in that NPCs series of waypoints.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Aug 12, 2002

//:://////////////////////////////////////////////

void GN_MoveToSpecificWayPoint(object oToMove, int nArrayNumber)

{

    int nLastWay = GetLocalNumber(oToMove, WALKWAYS_END_POINT);

    int nSeries = GetLocalNumber(oToMove, WALKWAYS_SERIES_NUMBER);

    string sString;

    if(nArrayNumber <= nLastWay)

    {

        if(nSeries > 0)

        {

            string sSeriesWay;

            if(nSeries < 10)

            {

                sSeriesWay = "0" + IntToString(nSeries);

            }

            else

            {

                sSeriesWay = IntToString(nSeries);

            }

            sString = "WP_" + sSeriesWay;

        }

        else

        {

            sString = "WP_" + GetTag(oToMove);

        }

        if(nArrayNumber < 10)

        {

            sString = sString + "_0" + IntToString(nArrayNumber);

        }

        else

        {

            sString = sString + "_" + IntToString(nArrayNumber);

        }



        object oWay = GetWaypointByTag(sString);

        if(GetIsObjectValid(oWay))

        {

            AssignCommand(oToMove, ClearAllActions());

            AssignCommand(oToMove, ActionMoveToObject(oWay, FALSE));

        }

    }

}



//::///////////////////////////////////////////////

//:: Get Waypooint Direction

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Determines the direction that a NPC should be

    walking along their waypoints.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Jul 20, 2002

//:://////////////////////////////////////////////



int GN_GetWayPointDirection(int nEndArray, int nCurrentPosition)

{

    int nDirection;

    int nFlag = GN_GetSpawnInCondition(SW_FLAG_WAYPOINT_DIRECTION);

    if(nEndArray == nCurrentPosition && nFlag == FALSE)

    {

        nDirection = -1;

        GN_SetSpawnInCondition(SW_FLAG_WAYPOINT_DIRECTION, TRUE);

    }

    else if(nCurrentPosition == 1 && nFlag == TRUE)

    {

        nDirection = 1;

        GN_SetSpawnInCondition(SW_FLAG_WAYPOINT_DIRECTION, FALSE);

    }

    else if(nFlag == FALSE)

    {

        nDirection = 1;

    }

    else if(nFlag == TRUE)

    {

        nDirection = -1;

    }



    return nDirection;

}



//::///////////////////////////////////////////////

//:: Set Up Way Points

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Used to initialize the NPCs waypoints

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: Oct 9, 2002

//:://////////////////////////////////////////////



void GN_SetUpWayPoints()

{

    string sString;

    int nSeries = GetLocalNumber(OBJECT_SELF, WALKWAYS_SERIES_NUMBER);

    if(nSeries > 0)

    {

        string sSeriesWay;

        if(nSeries < 10)

        {

            sSeriesWay = "0" + IntToString(nSeries);

        }

        else

        {

            sSeriesWay = IntToString(nSeries);

        }

        sString = "WP_" + sSeriesWay;

    }

    else

    {

        sString = "WP_" + GetTag(OBJECT_SELF);

    }



    int nCnt = 1;

    string sTest = sString + "_01";

    object oWay = GetWaypointByTag(sTest);



    while(GetIsObjectValid(oWay))

    {

        nCnt++;

        if(nCnt < 10)

        {

            sTest = sString + "_0" + IntToString(nCnt);

        }

        else

        {

            sTest = sString + "_" + IntToString(nCnt);

        }

        oWay = GetWaypointByTag(sTest);

    }

    nCnt = nCnt - 1;

    if(nCnt > 0)

    {

        SetLocalNumber(OBJECT_SELF, WALKWAYS_END_POINT, nCnt);

    }

}



//::///////////////////////////////////////////////

//:: Play Walk Ways Animations

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Plays an animation between way points

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: March 13, 2003

//:://////////////////////////////////////////////



void GN_PlayWalkWaysAnimation()

{

    int nRoll = d8();

    if(nRoll == 1)

    {

        //WK_MyPrintString("WALKWAYS DEBUG *************** Play Anim: Bored");

        ActionPlayAnimation(ANIMATION_FIREFORGET_PAUSE_BORED, 1.0);

    }

    else if(nRoll == 2)

    {

        //WK_MyPrintString("WALKWAYS DEBUG *************** Play Anim: Scratch");

        ActionPlayAnimation(ANIMATION_FIREFORGET_PAUSE_SCRATCH_HEAD, 1.0);

    }

    else if(nRoll == 3)

    {

        //WK_MyPrintString("WALKWAYS DEBUG *************** Play Anim: Pause 2");

        ActionPlayAnimation(ANIMATION_LOOPING_PAUSE2, 1.0, 3.0);

    }

    else if((nRoll == 4 || nRoll == 5) && GetRacialType(OBJECT_SELF) != RACIAL_TYPE_DROID)

    {

        if(GetGender(OBJECT_SELF) == GENDER_MALE)

        {

            //WK_MyPrintString("WALKWAYS DEBUG *************** Play Anim: Male Pause 3");

            GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, FALSE);

            ActionPlayAnimation(ANIMATION_LOOPING_PAUSE3, 1.0, 20.4);

            ActionDoCommand(GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, TRUE));

        }

        else if(GetGender(OBJECT_SELF) == GENDER_FEMALE)

        {

            //WK_MyPrintString("WALKWAYS DEBUG *************** Play Anim: Female Pause 3");

            GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, FALSE);

            ActionPlayAnimation(ANIMATION_LOOPING_PAUSE3, 1.0, 13.3);

            ActionDoCommand(GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, TRUE));

        }

    }

    else if(nRoll == 6 || nRoll == 4 || nRoll == 5)

    {

        //WK_MyPrintString("WALKWAYS DEBUG *************** Play Anim: Head Turn Left");

        ActionPlayAnimation(ANIMATION_FIREFORGET_HEAD_TURN_LEFT);

    }

    else if(nRoll == 7)

    {

        //WK_MyPrintString("WALKWAYS DEBUG *************** Play Anim: Head Turn Right");

        ActionPlayAnimation(ANIMATION_FIREFORGET_HEAD_TURN_RIGHT);

    }

    else if(nRoll == 8)

    {

        //WK_MyPrintString("WALKWAYS DEBUG *************** Play Anim: Pause 2");

        GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, FALSE);

        ActionPlayAnimation(ANIMATION_LOOPING_PAUSE2, 1.0, 5.0);

        ActionDoCommand(GN_SetSpawnInCondition(SW_FLAG_AMBIENT_ANIMATIONS, TRUE));

    }

}



//::///////////////////////////////////////////////

//:: Are Walk Ways Available

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Are valid walkway points available for walking

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: May 22, 2003

//:://////////////////////////////////////////////

int GN_CheckWalkWays(object oTarget)

{

    string sTag = "WP_" + GetTag(oTarget) + "_01";

    string sPost = "POST_" + GetTag(oTarget);

    int nSeriesInt = GetLocalNumber(oTarget, WALKWAYS_SERIES_NUMBER);

    string sSeriesWay;

    if(nSeriesInt < 10)

    {

        sSeriesWay = "0" + IntToString(nSeriesInt);

    }

    else

    {

        sSeriesWay = IntToString(nSeriesInt);

    }

    string sTestWay = "WP_" + sSeriesWay + "_01";



    object oWay = GetWaypointByTag(sTag);

    object oWay2 = GetWaypointByTag(sTestWay);

    object oPost = GetWaypointByTag(sPost);



    WK_MyPrintString("Walk Initiate for " + GetTag(oTarget));

    WK_MyPrintString("TAG WAY FOUND = " + IntToString(GetIsObjectValid(oWay)));

    WK_MyPrintString("WAY POINT NAME = " + GetTag(oWay));

    WK_MyPrintString("SERIES INT = " + IntToString(nSeriesInt));

    WK_MyPrintString("SERIES WAY FOUND = " + IntToString(GetIsObjectValid(oWay2)));

    WK_MyPrintString("SERIES Series Tag = " + sTestWay);

    WK_MyPrintString("");



    if(GetIsObjectValid(oWay) || GetIsObjectValid(oWay2) || GetIsObjectValid(oPost))

    {

        return TRUE;

    }

    return FALSE;

}



void WK_MyPrintString(string sString)

{

    if(!ShipBuild())

    {

        PrintString(sString);

    }

}

''',

    'k_inc_zone': b'''//:: k_inc_zones

/*

     Zone including for controlling

     the chaining of creatures

*/

//:: Created By: Preston Watamaniuk

//:: Copyright (c) 2002 Bioware Corp.



#include "k_inc_generic"



//Function run by the trigger to catalog the control nodes followers

void ZN_CatalogFollowers();

//Checks zone conditional on creature to if they belong to the zone

int ZN_CheckIsFollower(object oController, object oTarget);

//Checks the distance and creatures around the PC to see if it should return home.

int ZN_CheckReturnConditions();

//Gets the followers to move back to the controller object

void ZN_MoveToController(object oController, object oFollower);

//Checks to see if a specific individual needs to return to the controller.

int ZN_CheckFollowerReturnConditions(object oTarget);





//::///////////////////////////////////////////////

//:: Catalog Zone Followers

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

     Catalogs all creatures within

     the trigger area and marks

     them with an integer which

     is part of the creature's

     tag.

     Use local number SW_NUMBER_LAST_COMBO

     as a test. A new local number will

     be defined if the system works.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 7, 2003

//:://////////////////////////////////////////////

void ZN_CatalogFollowers()

{

    GN_PostString("FIRING", 10,10, 10.0);

    if(GetLocalBoolean(OBJECT_SELF, 10) == FALSE) //Has talked to boolean

    {

        string sZoneTag = GetTag(OBJECT_SELF);

        int nZoneNumber = StringToInt(GetStringRight(sZoneTag, 2));

        //Set up creature followers

        object oZoneFollower = GetFirstInPersistentObject();

        while(GetIsObjectValid(oZoneFollower))

        {

            SetLocalNumber(oZoneFollower, SW_NUMBER_COMBAT_ZONE, nZoneNumber);

            //GN_MyPrintString("ZONING DEBUG ***************** Setup Follower = " + GN_ReturnDebugName(oZoneFollower));

            //GN_MyPrintString("ZONING DEBUG ***************** Setup Follower Zone # = " + GN_ITS(GetLocalNumber(oZoneFollower, SW_NUMBER_COMBAT_ZONE)));



            oZoneFollower = GetNextInPersistentObject();

        }

        SetLocalBoolean(OBJECT_SELF, 10, TRUE);//Has talked to boolean

    }

}



//::///////////////////////////////////////////////

//:: Check Object for Zoning

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks the object to see if they part of the

    zone. This function is run off of the control

    node.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 7, 2003

//:://////////////////////////////////////////////

int ZN_CheckIsFollower(object oController, object oTarget)

{

    int nNumber = GetLocalNumber(oTarget, SW_NUMBER_COMBAT_ZONE);

    string sZoneTag = GetTag(OBJECT_SELF);

    int nZoneNumber = StringToInt(GetStringRight(sZoneTag, 2));

    if(nZoneNumber == nNumber)

    {

        return TRUE;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Check Return Conditions

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks to see if the conditions exist to

    possibly check for followers to return to

    the controller.

*/

//:://////////////////////////////////////////////



//:://////////////////////////////////////////////

int ZN_CheckReturnConditions()

{

    object oPC = GetPartyMemberByIndex(0);

    /*

        1.  Is the PC more than 21m away from the control node

        2.  Is the follower more than 20m away from the control node

        3.  Are there 9 or more individuals around the any single party member out to a distance of 30m

    */

    object oNinth = GetNearestCreature(CREATURE_TYPE_PLAYER_CHAR, PLAYER_CHAR_NOT_PC, oPC, 9);

    //GN_MyPrintString("ZONING DEBUG ***************** 9th Creature = " + GN_ReturnDebugName(oNinth));

    //GN_MyPrintString("ZONING DEBUG ***************** 9th Creature Distance = " + FloatToString(GetDistanceBetween(oPC, oNinth), 4,2));



    if(GetIsObjectValid(oNinth) && GetDistanceBetween(oPC, oNinth) < 30.0)

    {

        if(GetDistanceBetween(OBJECT_SELF, oPC) > 21.0)

        {

            return TRUE;

        }

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Check Follower Return Conditions.

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Checks if the follower object needs to return

    to home base.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 8, 2003

//:://////////////////////////////////////////////

int ZN_CheckFollowerReturnConditions(object oTarget)

{

    float fDistance = GetDistanceBetween(oTarget, OBJECT_SELF);

    //GN_MyPrintString("ZONING DEBUG ***************** " + GN_ReturnDebugName(oTarget) + " control distance " + FloatToString(fDistance, 4, 2));



    if(fDistance >= 10.0 && GetIsEnemy(oTarget, GetFirstPC()))

    {

        return TRUE;

    }

    return FALSE;

}



//::///////////////////////////////////////////////

//:: Move to Controller

//:: Copyright (c) 2001 Bioware Corp.

//:://////////////////////////////////////////////

/*

    Gets the follower object to move back to the

    controller object.

*/

//:://////////////////////////////////////////////

//:: Created By: Preston Watamaniuk

//:: Created On: April 7, 2003

//:://////////////////////////////////////////////

void ZN_MoveToController(object oController, object oFollower)

{

    //GN_MyPrintString("ZONING DEBUG ***************** Controller = " + GN_ReturnDebugName(oController));

    //GN_MyPrintString("ZONING DEBUG ***************** Follower = " + GN_ReturnDebugName(oFollower));

    //GN_MyPrintString("ZONING DEBUG ***************** Follower Zone # = " + GN_ITS(GetLocalNumber(oFollower, SW_NUMBER_LAST_COMBO)));

    if(GetCurrentAction(oFollower) != ACTION_INVALID)

    {

        SetCommandable(TRUE);

    }



    CancelCombat(oFollower);

    AssignCommand(oFollower, ClearAllActions());

    AssignCommand(oFollower, ActionForceMoveToObject(oController, TRUE, 5.0, 5.0));

    AssignCommand(oFollower, ActionDoCommand(SetCommandable(TRUE, oFollower)));

    AssignCommand(oFollower, SetCommandable(FALSE, oFollower));

}











''',

}