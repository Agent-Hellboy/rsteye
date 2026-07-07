[Setup]
AppName=RstEyeApp
AppVersion=1.0
DefaultDirName={pf}\RstEyeApp
DefaultGroupName=RstEyeApp
OutputDir=..\..\dist
OutputBaseFilename=RstEyeAppInstaller
Compression=lzma
SolidCompression=yes

[Files]
Source: "..\..\dist\RstEyeApp.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\RstEyeApp"; Filename: "{app}\RstEyeApp.exe"

[Run]
Filename: "{app}\RstEyeApp.exe"; Description: "{cm:LaunchProgram,RstEyeApp}"; Flags: nowait postinstall skipifsilent

[Code]
const
  ServiceName = 'RstEyeAppService';

function IsServiceInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('sc', 'query ' + ServiceName, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function InstallService: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('sc', 'create ' + ServiceName + ' binPath= "' + ExpandConstant('{app}\RstEyeApp.exe') + '" start= auto', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function StartService: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('sc', 'start ' + ServiceName, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not IsServiceInstalled then
    begin
      if InstallService then
      begin
        MsgBox('Service installed successfully.', mbInformation, MB_OK);
      end
      else
      begin
        MsgBox('Failed to install service.', mbError, MB_OK);
      end;
    end;

    if IsServiceInstalled then
    begin
      if StartService then
      begin
        MsgBox('Service started successfully.', mbInformation, MB_OK);
      end
      else
      begin
        MsgBox('Failed to start service.', mbError, MB_OK);
      end;
    end;
  end;
end;
