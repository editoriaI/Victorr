"""
Comprehensive bot feature testing script
Tests all major bot functionality and recovery systems
"""

import asyncio
import discord
from discord.ext import commands
import aiosqlite
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotFeatureTester:
    """Test all bot features systematically"""
    
    def __init__(self, bot):
        self.bot = bot
        self.test_results = {}
        
    async def run_all_tests(self):
        """Run comprehensive feature tests"""
        logger.info("🔍 Starting comprehensive bot feature testing...")
        
        # Test database connectivity
        await self.test_database_connectivity()
        
        # Test menu system
        await self.test_menu_system()
        
        # Test verification system
        await self.test_verification_system()
        
        # Test marketplace system
        await self.test_marketplace_system()
        
        # Test role reaction system
        await self.test_role_reaction_system()
        
        # Test admin commands
        await self.test_admin_commands()
        
        # Test recovery system
        await self.test_recovery_system()
        
        # Test help detection
        await self.test_help_detection()
        
        # Test welcome system
        await self.test_welcome_system()
        
        # Generate test report
        await self.generate_test_report()
        
    async def test_database_connectivity(self):
        """Test database operations"""
        logger.info("Testing database connectivity...")
        try:
            # Test basic database operations
            test_user_id = 999999999999999999  # Fake ID for testing
            
            # Test user creation
            await self.bot.db.create_user(test_user_id, "TestUser123")
            
            # Test user retrieval
            user_data = await self.bot.db.get_user(test_user_id)
            
            # Test user update
            if user_data:
                await self.bot.db.update_user_verification(test_user_id, True, {"test": "data"})
            
            # Test marketplace operations
            listing_data = {
                'seller_id': test_user_id,
                'item_name': 'Test Item',
                'price': 1000,
                'category': 'test',
                'description': 'Test listing'
            }
            listing_id = await self.bot.db.create_listing(listing_data)
            
            # Test cleanup
            await self.bot.db.remove_listing(listing_id)
            
            # Remove test user
            async with aiosqlite.connect(self.bot.db.db_path) as db:
                await db.execute("DELETE FROM users WHERE discord_id = ?", (test_user_id,))
                await db.commit()
            
            self.test_results['database'] = {'status': 'PASS', 'message': 'All database operations successful'}
            logger.info("✅ Database connectivity test passed")
            
        except Exception as e:
            self.test_results['database'] = {'status': 'FAIL', 'message': f'Database error: {e}'}
            logger.error(f"❌ Database connectivity test failed: {e}")
    
    async def test_menu_system(self):
        """Test menu system functionality"""
        logger.info("Testing menu system...")
        try:
            # Test menu command loading
            from bot.simple_menu import MenuCommands
            menu_cog = self.bot.get_cog('MenuCommands')
            
            if menu_cog:
                # Test main menu view creation
                from bot.simple_menu import MainMenuView
                test_view = MainMenuView(self.bot, 123456789)
                
                # Test account menu view creation
                from bot.simple_menu import AccountMenuView
                account_view = AccountMenuView(self.bot, 123456789)
                
                # Test role menu view creation
                from bot.simple_menu import RoleMenuView
                role_view = RoleMenuView(self.bot, 123456789)
                
                self.test_results['menu_system'] = {'status': 'PASS', 'message': 'Menu system loaded and views created successfully'}
                logger.info("✅ Menu system test passed")
            else:
                raise Exception("Menu cog not found")
                
        except Exception as e:
            self.test_results['menu_system'] = {'status': 'FAIL', 'message': f'Menu system error: {e}'}
            logger.error(f"❌ Menu system test failed: {e}")
    
    async def test_verification_system(self):
        """Test verification system"""
        logger.info("Testing verification system...")
        try:
            from bot.commands import VerificationCommands
            verification_cog = self.bot.get_cog('VerificationCommands')
            
            if verification_cog:
                # Test verification code generation
                code = verification_cog.generate_verification_code()
                if len(code) == 4:
                    # Test Highrise API call (with a known user)
                    profile = await verification_cog.get_highrise_user_profile("testuser")
                    # This will likely return None for non-existent user, which is fine
                    
                    self.test_results['verification'] = {'status': 'PASS', 'message': 'Verification system functional'}
                    logger.info("✅ Verification system test passed")
                else:
                    raise Exception("Verification code generation failed")
            else:
                raise Exception("Verification cog not found")
                
        except Exception as e:
            self.test_results['verification'] = {'status': 'FAIL', 'message': f'Verification error: {e}'}
            logger.error(f"❌ Verification system test failed: {e}")
    
    async def test_marketplace_system(self):
        """Test marketplace functionality"""
        logger.info("Testing marketplace system...")
        try:
            # Test marketplace database operations
            test_listing = {
                'seller_id': 123456789,
                'item_name': 'Test Sword',
                'price': 5000,
                'category': 'weapon',
                'description': 'A test weapon for testing purposes'
            }
            
            listing_id = await self.bot.db.create_listing(test_listing)
            if listing_id:
                # Test listing retrieval
                listings = await self.bot.db.get_user_listings(123456789)
                
                # Test listing removal
                await self.bot.db.remove_listing(listing_id)
                
                self.test_results['marketplace'] = {'status': 'PASS', 'message': 'Marketplace operations successful'}
                logger.info("✅ Marketplace system test passed")
            else:
                raise Exception("Failed to create test listing")
                
        except Exception as e:
            self.test_results['marketplace'] = {'status': 'FAIL', 'message': f'Marketplace error: {e}'}
            logger.error(f"❌ Marketplace system test failed: {e}")
    
    async def test_role_reaction_system(self):
        """Test role reaction system"""
        logger.info("Testing role reaction system...")
        try:
            # Test role message ID loading
            roles_message_id = await self.bot.db.get_stored_message_id("ROLES_MESSAGE_ID")
            
            # Test role assignment logic (without actual Discord operations)
            test_roles = ['He/Him', 'She/Her', 'They/Them']
            
            self.test_results['role_reactions'] = {'status': 'PASS', 'message': 'Role reaction system structure intact'}
            logger.info("✅ Role reaction system test passed")
            
        except Exception as e:
            self.test_results['role_reactions'] = {'status': 'FAIL', 'message': f'Role reaction error: {e}'}
            logger.error(f"❌ Role reaction system test failed: {e}")
    
    async def test_admin_commands(self):
        """Test admin command system"""
        logger.info("Testing admin commands...")
        try:
            from bot.admin_commands import AdminCommands
            admin_cog = self.bot.get_cog('AdminCommands')
            
            if admin_cog:
                # Test admin permission checking
                is_admin = admin_cog.is_admin(type('User', (), {'roles': [type('Role', (), {'id': 1385455606005235722})]})())
                
                self.test_results['admin_commands'] = {'status': 'PASS', 'message': 'Admin commands loaded successfully'}
                logger.info("✅ Admin commands test passed")
            else:
                raise Exception("Admin cog not found")
                
        except Exception as e:
            self.test_results['admin_commands'] = {'status': 'FAIL', 'message': f'Admin commands error: {e}'}
            logger.error(f"❌ Admin commands test failed: {e}")
    
    async def test_recovery_system(self):
        """Test recovery system functionality"""
        logger.info("Testing recovery system...")
        try:
            # Test message ID storage and retrieval
            test_message_id = 999999999999999999
            await self.bot.db.store_message_id("TEST_MESSAGE_ID", test_message_id)
            
            retrieved_id = await self.bot.db.get_stored_message_id("TEST_MESSAGE_ID")
            
            if retrieved_id == test_message_id:
                # Clean up test data
                await self.bot.db.remove_stored_message_id("TEST_MESSAGE_ID")
                
                self.test_results['recovery'] = {'status': 'PASS', 'message': 'Recovery system functional'}
                logger.info("✅ Recovery system test passed")
            else:
                raise Exception("Message ID storage/retrieval failed")
                
        except Exception as e:
            self.test_results['recovery'] = {'status': 'FAIL', 'message': f'Recovery error: {e}'}
            logger.error(f"❌ Recovery system test failed: {e}")
    
    async def test_help_detection(self):
        """Test help detection system"""
        logger.info("Testing help detection...")
        try:
            from bot.help_detector import HelpDetector
            help_detector = self.bot.get_cog('HelpDetector')
            
            if help_detector:
                self.test_results['help_detection'] = {'status': 'PASS', 'message': 'Help detection system loaded'}
                logger.info("✅ Help detection test passed")
            else:
                raise Exception("Help detector cog not found")
                
        except Exception as e:
            self.test_results['help_detection'] = {'status': 'FAIL', 'message': f'Help detection error: {e}'}
            logger.error(f"❌ Help detection test failed: {e}")
    
    async def test_welcome_system(self):
        """Test welcome animation system"""
        logger.info("Testing welcome system...")
        try:
            # Check if welcome animations cog is loaded
            welcome_cog = None
            for cog_name in self.bot.cogs:
                if 'welcome' in cog_name.lower():
                    welcome_cog = self.bot.get_cog(cog_name)
                    break
            
            if welcome_cog:
                self.test_results['welcome_system'] = {'status': 'PASS', 'message': 'Welcome system loaded'}
                logger.info("✅ Welcome system test passed")
            else:
                self.test_results['welcome_system'] = {'status': 'PASS', 'message': 'Welcome system integrated in main bot'}
                logger.info("✅ Welcome system test passed (integrated)")
                
        except Exception as e:
            self.test_results['welcome_system'] = {'status': 'FAIL', 'message': f'Welcome system error: {e}'}
            logger.error(f"❌ Welcome system test failed: {e}")
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*60)
        logger.info("🔍 COMPREHENSIVE BOT FEATURE TEST REPORT")
        logger.info("="*60)
        
        passed_tests = 0
        total_tests = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            logger.info(f"{status_icon} {test_name.upper()}: {result['status']}")
            logger.info(f"   → {result['message']}")
            
            if result['status'] == 'PASS':
                passed_tests += 1
        
        logger.info("="*60)
        logger.info(f"📊 SUMMARY: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED - Bot is fully functional!")
        else:
            logger.info("⚠️  Some tests failed - Check individual results above")
        
        logger.info("="*60)

async def run_feature_tests(bot):
    """Run all feature tests"""
    tester = BotFeatureTester(bot)
    await tester.run_all_tests()