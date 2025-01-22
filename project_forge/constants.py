from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

SUPPORTED_LANGUAGES = [
	{
		"name": "Golang",
		"template_folder": "go"
	},
	{
		"name": "C#",
		"template_folder": "csharp"
	},
	{
		"name": "Python",
		"template_folder": "python"
	},
	{
		"name": "Javascript",
		"template_folder": "javascript"
	}
]
