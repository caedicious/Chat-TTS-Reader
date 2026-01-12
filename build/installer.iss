; Chat TTS Reader - Inno Setup Script
; Creates a professional Windows installer

#define MyAppName "Chat TTS Reader"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "caedicious"
#define MyAppURL "https://github.com/caedicious/Chat-TTS-Reader"
#define MyAppExeName "ChatTTSReader.exe"

[Setup]
; Application info
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases

; Installation settings
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Output settings
OutputDir=installer_output
OutputBaseFilename=ChatTTSReader-Setup-{#MyAppVersion}
;SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes

; Wizard settings
WizardStyle=modern
WizardSizePercent=120,120

; Uninstaller
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; Other
LicenseFile=LICENSE.txt
InfoBeforeFile=INSTALL_INFO.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start automatically when Windows starts"; GroupDescription: "Startup:"; Flags: unchecked
Name: "startupwaitforlive"; Description: "Wait for Twitch live before starting (press ENTER to bypass)"; GroupDescription: "Startup:"; Flags: unchecked exclusive
Name: "startupimmediate"; Description: "Start immediately on boot"; GroupDescription: "Startup:"; Flags: unchecked exclusive

[Files]
; Main application files (update path after building)
Source: "dist\ChatTTSReader-Final\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Additional files
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Configure"; Filename: "{app}\Configure.exe"
Name: "{group}\Kick Login"; Filename: "{app}\KickLogin.exe"
Name: "{group}\Audio Test"; Filename: "{app}\AudioTest.exe"
Name: "{group}\Wait For Live"; Filename: "{app}\WaitForLive.exe"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Startup - Wait for Live
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\WaitForLive.exe"; Tasks: startupwaitforlive

; Startup - Immediate
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupimmediate

[Run]
; Run configuration after install
Filename: "{app}\Configure.exe"; Description: "Configure stream platforms now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up config directory (includes config.json and kick_cookies.json)
Type: filesandordirs; Name: "{userprofile}\.chat-tts-reader"

[Code]
// Custom wizard page for Twitch setup
var
  TwitchPage: TInputQueryWizardPage;
  TwitchSetupCheckbox: TNewCheckBox;

procedure InitializeWizard;
begin
  // Create Twitch setup page
  TwitchPage := CreateInputQueryPage(wpSelectTasks,
    'Twitch Live Detection',
    'Automatically start when you go live on Twitch',
    'Enter your Twitch information below. This allows the app to detect when you start streaming.' + #13#10 + #13#10 +
    'You can always press ENTER to bypass and start immediately.' + #13#10 + #13#10 +
    'To get a Client ID:' + #13#10 +
    '1. Go to dev.twitch.tv/console/apps' + #13#10 +
    '2. Register a new application' + #13#10 +
    '3. Set OAuth Redirect to http://localhost' + #13#10 +
    '4. Copy the Client ID' + #13#10 + #13#10 +
    'Leave blank to skip this step.');
  TwitchPage.Add('Twitch Client ID:', False);
  TwitchPage.Add('Twitch Username:', False);
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  // Skip Twitch page if neither startup option is selected
  if PageID = TwitchPage.ID then
  begin
    Result := not (WizardIsTaskSelected('startupwaitforlive') or WizardIsTaskSelected('startupimmediate'));
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ClientID, Username: String;
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Save Twitch credentials if provided
    ClientID := TwitchPage.Values[0];
    Username := TwitchPage.Values[1];
    
    if (ClientID <> '') and (Username <> '') then
    begin
      // Save credentials using the app's setup
      // We'll create a simple batch file to do this
      SaveStringToFile(ExpandConstant('{app}\setup_twitch_creds.bat'),
        '@echo off' + #13#10 +
        'cd /d "' + ExpandConstant('{app}') + '"' + #13#10 +
        'echo Setting up Twitch credentials...' + #13#10 +
        'python -c "import keyring; keyring.set_password(''ChatTTSReader'', ''twitch_client_id'', ''' + ClientID + ''')"' + #13#10 +
        'python -c "import keyring; keyring.set_password(''ChatTTSReader'', ''twitch_username'', ''' + Username + ''')"' + #13#10 +
        'echo Done!' + #13#10,
        False);
    end;
  end;
end;

// Clean up credentials on uninstall
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Try to clean up keyring credentials
    Exec('python', '-c "import keyring; keyring.delete_password(''ChatTTSReader'', ''twitch_client_id'')"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('python', '-c "import keyring; keyring.delete_password(''ChatTTSReader'', ''twitch_username'')"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
