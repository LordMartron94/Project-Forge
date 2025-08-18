from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).parent

INTERNAL_PATH: Path = PROJECT_ROOT / "_internal"

SCRIPTS_DIR = PROJECT_ROOT / "scripts"

SUPPORTED_LANGUAGES = [
	{
		"group_name": "Systems & Low-Level Programming",
		"description": "Languages used for operating systems, embedded systems, and performance-critical applications.",
		"languages": [
			{
				"name": "C89",
				"template_folder": "c89"
			},
			{
				"name": "Golang",
				"template_folder": "go"
			}
		]
	},
	{
		"group_name": "General-Purpose & Application Development",
		"description": "Versatile, often object-oriented languages for building desktop, backend, and enterprise software.",
		"languages": [
			{
				"name": "C#",
				"template_folder": "csharp"
			}
		]
	},
	{
		"group_name": "Scripting & Web Development",
		"description": "High-level languages ideal for web applications, automation, and rapid development.",
		"languages": [
			{
				"name": "Python",
				"template_folder": "python"
			},
			{
				"name": "Javascript",
				"template_folder": "javascript"
			}
		]
	},
	{
		"group_name": "Functional Programming",
		"description": "Languages that treat computation as the evaluation of mathematical functions and avoid changing-state.",
		"languages": []
	},
	{
		"group_name": "Mobile Development",
		"description": "Languages specifically designed or commonly used for creating applications on mobile devices.",
		"languages": []
	}
]
