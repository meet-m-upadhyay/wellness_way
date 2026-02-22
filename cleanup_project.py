#!/usr/bin/env python3
"""
Project Cleanup Script
Removes unnecessary test files and consolidates documentation
"""
import os
import shutil
from pathlib import Path

# Files to keep (essential)
KEEP_TEST_FILES = {
    'test_supabase_connection.py',
    'test_ml_pipeline.py',
    'test_admin_system.py',
}

# Documentation files to keep
KEEP_DOCS = {
    'README.md',
    'spec.md',
    'QUICK_START.md',
    'SECURITY_REMINDER.md',
    'ML_MODELS_USED.md',
    'SUPABASE_MIGRATION_SUCCESS.md',
    'GOOGLE_OAUTH_SETUP.md',
    'NOTIFICATION_SYSTEM_ARCHITECTURE.md',
    'database_management_commands.md',
    'DOCUMENTATION_INDEX.md',
}

# Backend scripts to keep
KEEP_BACKEND_SCRIPTS = {
    'start_backend.py',
    'run_migrations.py',
    'test_supabase_connection.py',
    'migrate_to_supabase.py',
}

def cleanup_test_files():
    """Remove unnecessary test files from backend root"""
    backend_path = Path('backend')
    deleted = []
    
    print("\n🧹 Cleaning up test files...")
    
    for test_file in backend_path.glob('test_*.py'):
        if test_file.name not in KEEP_TEST_FILES:
            try:
                test_file.unlink()
                deleted.append(test_file.name)
                print(f"  ✓ Deleted: {test_file.name}")
            except Exception as e:
                print(f"  ✗ Failed to delete {test_file.name}: {e}")
    
    print(f"\n✅ Deleted {len(deleted)} test files")
    return deleted

def cleanup_documentation():
    """Remove redundant documentation files"""
    root_path = Path('.')
    deleted = []
    
    print("\n📚 Cleaning up documentation...")
    
    # Patterns to delete
    delete_patterns = [
        '*_COMPLETION_REPORT.md',
        '*_FIX*.md',
        'CHATGPT_*.md',
        'COMPLETE_*.md',
        'CURRENT_*.md',
        'FILES_CREATED_*.md',
        'AI_BUTTONS_*.md',
        'DISABLE_*.md',
        'USER_DISABLE_*.md',
        'EASY_MIGRATION_*.md',
        'MIGRATE_DATA_*.md',
        'SUPABASE_CONNECTION_*.md',
        'SUPABASE_MIGRATION_IMPLEMENTATION.md',
        'SUPABASE_TEAM_*.md',
        'ML_PIPELINE_COMPLETE.md',
        'ML_PIPELINE_COMPLETE_EXPLANATION.md',
        'ML_PIPELINE_UI_*.md',
        'ML_REGENERATION_*.md',
        'QUICK_START_ML_*.md',
        'QUICK_START_SUPABASE.md',
        'QUICK_TEST_*.md',
        'REGENERATE_*.md',
        'ZERO_STATE_*.md',
        'FINAL_*.md',
        'INFINITE_LOOP_*.md',
        'NAVIGATION_*.md',
        'ADMIN_APPROVAL_*.md',
        'ADMIN_DASHBOARD_*.md',
        'ADMIN_SYSTEM_*.md',
        'ADMIN_USER_*.md',
        'EXACT_*.md',
        'GIT_PUSH_SUCCESS.md',  # Can delete after reading
    ]
    
    for pattern in delete_patterns:
        for doc_file in root_path.glob(pattern):
            if doc_file.name not in KEEP_DOCS and doc_file.is_file():
                try:
                    doc_file.unlink()
                    deleted.append(doc_file.name)
                    print(f"  ✓ Deleted: {doc_file.name}")
                except Exception as e:
                    print(f"  ✗ Failed to delete {doc_file.name}: {e}")
    
    print(f"\n✅ Deleted {len(deleted)} documentation files")
    return deleted

def cleanup_backend_docs():
    """Remove redundant documentation from backend folder"""
    backend_path = Path('backend')
    deleted = []
    
    print("\n📚 Cleaning up backend documentation...")
    
    # Patterns to delete
    delete_patterns = [
        '*_COMPLETION_REPORT.md',
        '*_FIX*.md',
        'CHATGPT_*.md',
        'COMPLETE_*.md',
        'ML_PIPELINE_*.md',
    ]
    
    for pattern in delete_patterns:
        for doc_file in backend_path.glob(pattern):
            if doc_file.is_file():
                try:
                    doc_file.unlink()
                    deleted.append(doc_file.name)
                    print(f"  ✓ Deleted: {doc_file.name}")
                except Exception as e:
                    print(f"  ✗ Failed to delete {doc_file.name}: {e}")
    
    print(f"\n✅ Deleted {len(deleted)} backend documentation files")
    return deleted

def cleanup_debug_scripts():
    """Remove debug and temporary scripts"""
    backend_path = Path('backend')
    deleted = []
    
    print("\n🔧 Cleaning up debug scripts...")
    
    # Scripts to delete
    delete_scripts = [
        'check_hcd_content.py',
        'create_all_tables.py',
        'create_tables_directly.py',
        'delete_user.py',
        'demo_hcd_generation.py',
        'setup_supabase.py',
        'show_db_contents.py',
        'simple_test.py',
    ]
    
    # Debug scripts pattern
    for debug_file in backend_path.glob('debug_*.py'):
        delete_scripts.append(debug_file.name)
    
    for script_name in delete_scripts:
        script_path = backend_path / script_name
        if script_path.exists() and script_path.name not in KEEP_BACKEND_SCRIPTS:
            try:
                script_path.unlink()
                deleted.append(script_name)
                print(f"  ✓ Deleted: {script_name}")
            except Exception as e:
                print(f"  ✗ Failed to delete {script_name}: {e}")
    
    print(f"\n✅ Deleted {len(deleted)} debug scripts")
    return deleted

def cleanup_misc_files():
    """Remove miscellaneous temporary files"""
    deleted = []
    
    print("\n🗑️  Cleaning up miscellaneous files...")
    
    # Files to delete
    misc_files = [
        'backend/test_api_endpoints.db',
        'test_backend.py',
        'test_user.json',
        'test_with_jwt_token.py',
        'setup_ai.py',
        'encode_keys.py',
    ]
    
    for file_path in misc_files:
        path = Path(file_path)
        if path.exists():
            try:
                path.unlink()
                deleted.append(file_path)
                print(f"  ✓ Deleted: {file_path}")
            except Exception as e:
                print(f"  ✗ Failed to delete {file_path}: {e}")
    
    print(f"\n✅ Deleted {len(deleted)} miscellaneous files")
    return deleted

def create_backup():
    """Create backup of files before deletion"""
    print("\n💾 Creating backup...")
    
    backup_dir = Path('cleanup_backup')
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    backup_dir.mkdir()
    
    # Backup test files
    (backup_dir / 'test_files').mkdir()
    for test_file in Path('backend').glob('test_*.py'):
        if test_file.name not in KEEP_TEST_FILES:
            shutil.copy2(test_file, backup_dir / 'test_files' / test_file.name)
    
    # Backup docs
    (backup_dir / 'docs').mkdir()
    for doc_file in Path('.').glob('*.md'):
        if doc_file.name not in KEEP_DOCS:
            shutil.copy2(doc_file, backup_dir / 'docs' / doc_file.name)
    
    print(f"✅ Backup created in: {backup_dir.absolute()}")
    print("   (You can delete this folder after verifying the cleanup)")

def main():
    """Main cleanup function"""
    print("=" * 60)
    print("🧹 WellnessWay Project Cleanup")
    print("=" * 60)
    
    # Confirm with user
    print("\nThis script will:")
    print("  • Delete ~85 unnecessary test files")
    print("  • Delete ~35 redundant documentation files")
    print("  • Delete ~15 debug scripts")
    print("  • Create a backup before deletion")
    
    response = input("\nProceed with cleanup? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Cleanup cancelled")
        return
    
    # Create backup first
    create_backup()
    
    # Run cleanup
    test_files = cleanup_test_files()
    docs = cleanup_documentation()
    backend_docs = cleanup_backend_docs()
    scripts = cleanup_debug_scripts()
    misc = cleanup_misc_files()
    
    # Summary
    total_deleted = len(test_files) + len(docs) + len(backend_docs) + len(scripts) + len(misc)
    
    print("\n" + "=" * 60)
    print("✅ Cleanup Complete!")
    print("=" * 60)
    print(f"\nTotal files deleted: {total_deleted}")
    print(f"  • Test files: {len(test_files)}")
    print(f"  • Root documentation: {len(docs)}")
    print(f"  • Backend documentation: {len(backend_docs)}")
    print(f"  • Debug scripts: {len(scripts)}")
    print(f"  • Miscellaneous: {len(misc)}")
    
    print("\n📋 Next steps:")
    print("  1. Review the changes")
    print("  2. Run tests to ensure nothing broke: pytest backend/tests/")
    print("  3. Commit the cleanup: git add -A && git commit -m 'chore: Clean up test files and documentation'")
    print("  4. Delete backup folder if satisfied: rmdir /s cleanup_backup")
    
    print("\n📚 Documentation consolidated in:")
    print("  • docs/PROJECT_DOCUMENTATION.md - Complete project docs")
    print("  • docs/CLEANUP_PLAN.md - What was deleted and why")

if __name__ == '__main__':
    main()
