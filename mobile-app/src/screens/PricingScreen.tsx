/**
 * DEDAN Health 2.0 - Mobile Pricing Screen
 * React Native pricing UI with 14-day free trial and Ethiopia bank support
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
  Modal,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

interface PricingTier {
  tier: string;
  name: string;
  price_range: {
    min: number;
    max: number;
    currency: string;
  };
  features: string[];
  limits: Record<string, any>;
  is_popular: boolean;
  trial_available: boolean;
}

const { width } = Dimensions.get('window');

const PricingScreen: React.FC = () => {
  const navigation = useNavigation();
  const [pricingTiers, setPricingTiers] = useState<PricingTier[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTier, setSelectedTier] = useState<string>('');
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  useEffect(() => {
    loadPricingData();
  }, []);

  const loadPricingData = async () => {
    try {
      // Mock data - replace with actual API call
      const mockTiers: PricingTier[] = [
        {
          tier: 'starter',
          name: 'Starter Clinic',
          price_range: { min: 75, max: 150, currency: 'USD' },
          features: [
            'Basic DEDAN triage',
            'Safety-Guard AI',
            'WhatsApp/SMS gateway',
            'Clinic Console (up to 2 staff)',
            '1,000 triages/month',
            'Email support'
          ],
          limits: {
            staff_users: 2,
            triages_per_month: 1000,
            api_calls_per_month: 5000,
            storage_gb: 10
          },
          is_popular: false,
          trial_available: true
        },
        {
          tier: 'professional',
          name: 'Professional Clinic',
          price_range: { min: 250, max: 500, currency: 'USD' },
          features: [
            'All Starter features',
            'Risk-Prediction AI',
            'Chronic-Care Coach',
            'Higher usage limit (~10,000 triages/month)',
            'Priority email support',
            'Advanced analytics',
            'Multi-language support'
          ],
          limits: {
            staff_users: 10,
            triages_per_month: 10000,
            api_calls_per_month: 50000,
            storage_gb: 50
          },
          is_popular: true,
          trial_available: true
        },
        {
          tier: 'enterprise',
          name: 'Enterprise Clinic',
          price_range: { min: 1000, max: 3000, currency: 'USD' },
          features: [
            'All Professional features',
            'Image-Analysis AI',
            'Explainability AI',
            'Bias-Monitoring',
            'Multi-clinic hub',
            'API access',
            'Dedicated support',
            'Custom integrations',
            'White-label options'
          ],
          limits: {
            staff_users: -1,
            triages_per_month: -1,
            api_calls_per_month: -1,
            storage_gb: -1
          },
          is_popular: false,
          trial_available: true
        }
      ];
      
      setPricingTiers(mockTiers);
    } catch (error) {
      console.error('Failed to load pricing data:', error);
      Alert.alert('Error', 'Failed to load pricing information');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = (tier: string) => {
    setSelectedTier(tier);
    setShowPaymentModal(true);
  };

  const startTrial = async (tier: string) => {
    try {
      setLoading(true);
      
      // API call to start trial
      // const response = await apiService.post('/billing/start-trial', { tier });
      
      Alert.alert(
        'Trial Started!',
        'Your 14-day free trial has been activated. You can now use all Professional features.',
        [
          {
            text: 'OK',
            onPress: () => {
              setShowPaymentModal(false);
              navigation.navigate('Dashboard');
            }
          }
        ]
      );
    } catch (error) {
      console.error('Failed to start trial:', error);
      Alert.alert('Error', 'Failed to start trial. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (tier: PricingTier) => {
    const { min, max, currency } = tier.price_range;
    if (min === max) {
      return `$${min}/${currency}`;
    }
    return `$${min}-${max}/${currency}`;
  };

  const PricingCard = ({ tier, onPress }: { tier: PricingTier; onPress: () => void }) => (
    <TouchableOpacity
      style={[
        styles.card,
        tier.is_popular && styles.popularCard
      ]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      {tier.is_popular && (
        <View style={styles.popularBadge}>
          <Text style={styles.popularBadgeText}>MOST POPULAR</Text>
        </View>
      )}

      <Text style={styles.planName}>{tier.name}</Text>
      
      <View style={styles.priceContainer}>
        <Text style={styles.price}>{formatPrice(tier)}</Text>
        <Text style={styles.pricePeriod}>per month</Text>
      </View>

      <View style={styles.featuresContainer}>
        <Text style={styles.sectionTitle}>Features:</Text>
        {tier.features.map((feature, index) => (
          <View key={index} style={styles.featureItem}>
            <Text style={styles.checkmark}>✓</Text>
            <Text style={styles.featureText}>{feature}</Text>
          </View>
        ))}
      </View>

      <View style={styles.limitsContainer}>
        <Text style={styles.sectionTitle}>Usage Limits:</Text>
        {tier.limits.staff_users !== -1 && (
          <Text style={styles.limitText}>
            <Text style={styles.limitLabel}>Staff Users:</Text> {tier.limits.staff_users}
          </Text>
        )}
        {tier.limits.triages_per_month !== -1 && (
          <Text style={styles.limitText}>
            <Text style={styles.limitLabel}>Triages/Month:</Text> {tier.limits.triages_per_month.toLocaleString()}
          </Text>
        )}
        {tier.limits.storage_gb !== -1 && (
          <Text style={styles.limitText}>
            <Text style={styles.limitLabel}>Storage:</Text> {tier.limits.storage_gb} GB
          </Text>
        )}
        {(tier.limits.staff_users === -1 || 
          tier.limits.triages_per_month === -1 || 
          tier.limits.storage_gb === -1) && (
          <Text style={styles.unlimitedText}>✓ Unlimited usage</Text>
        )}
      </View>

      <TouchableOpacity
        style={[
          styles.selectButton,
          tier.is_popular && styles.popularButton
        ]}
        onPress={onPress}
      >
        <Text style={[
          styles.selectButtonText,
          tier.is_popular && styles.popularButtonText
        ]}>
          {tier.trial_available ? 'Start 14-Day Free Trial' : 'Select Plan'}
        </Text>
      </TouchableOpacity>
    </TouchableOpacity>
  );

  const PaymentModal = () => (
    <Modal
      visible={showPaymentModal}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setShowPaymentModal(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>Start Your Free Trial</Text>
          
          <Text style={styles.modalDescription}>
            Get 14 days of full access to DEDAN Health Professional features. 
            No credit card required for trial.
          </Text>

          <Text style={styles.paymentMethodTitle}>Choose Payment Method for After Trial:</Text>
          
          <View style={styles.paymentMethods}>
            <TouchableOpacity
              style={styles.paymentOption}
              onPress={() => startTrial(selectedTier)}
            >
              <Text style={styles.paymentOptionTitle}>💳 Credit/Debit Card (Global)</Text>
              <Text style={styles.paymentOptionDescription}>Secure payment via Stripe</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.paymentOption}
              onPress={() => startTrial(selectedTier)}
            >
              <Text style={styles.paymentOptionTitle}>🏦 Bank Transfer (Ethiopia)</Text>
              <Text style={styles.paymentOptionDescription}>Commercial Bank, Awash Bank, Dashen Bank</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.paymentOption}
              onPress={() => startTrial(selectedTier)}
            >
              <Text style={styles.paymentOptionTitle}>📱 Mobile Wallet (Ethiopia)</Text>
              <Text style={styles.paymentOptionDescription}>Telebirr and other mobile money services</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.modalButtons}>
            <TouchableOpacity
              style={[styles.modalButton, styles.cancelButton]}
              onPress={() => setShowPaymentModal(false)}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modalButton, styles.startTrialButton]}
              onPress={() => startTrial(selectedTier)}
            >
              <Text style={styles.startTrialButtonText}>Start Trial</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading pricing...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Text style={styles.title}>Choose Your DEDAN Health Plan</Text>
        <Text style={styles.subtitle}>
          World-class AI-powered healthcare triage for clinics of all sizes. 
          Start with a 14-day free trial.
        </Text>
      </View>

      <View style={styles.pricingContainer}>
        {pricingTiers.map((tier) => (
          <PricingCard
            key={tier.tier}
            tier={tier}
            onPress={() => handleSelectPlan(tier.tier)}
          />
        ))}
      </View>

      {/* Ethiopia Bank Details */}
      <View style={styles.bankDetailsContainer}>
        <Text style={styles.bankDetailsTitle}>🇪🇹 Ethiopia Bank Transfer Details</Text>
        
        <View style={styles.bankSection}>
          <Text style={styles.bankName}>Commercial Bank of Ethiopia:</Text>
          <Text style={styles.bankInfo}>Account Name: DEDAN Health PLC</Text>
          <Text style={styles.bankInfo}>Account Number: 1000123456789</Text>
          <Text style={styles.bankInfo}>Branch: Addis Ababa Main Branch</Text>
          <Text style={styles.bankInfo}>SWIFT: CBETETAA</Text>
        </View>

        <View style={styles.bankSection}>
          <Text style={styles.bankName}>Awash Bank:</Text>
          <Text style={styles.bankInfo}>Account Name: DEDAN Health PLC</Text>
          <Text style={styles.bankInfo}>Account Number: 2000123456789</Text>
          <Text style={styles.bankInfo}>Branch: Addis Ababa HQ</Text>
          <Text style={styles.bankInfo}>SWIFT: AWASETAA</Text>
        </View>

        <View style={styles.bankSection}>
          <Text style={styles.bankName}>Dashen Bank:</Text>
          <Text style={styles.bankInfo}>Account Name: DEDAN Health PLC</Text>
          <Text style={styles.bankInfo}>Account Number: 3000123456789</Text>
          <Text style={styles.bankInfo}>Branch: Bole Branch</Text>
          <Text style={styles.bankInfo}>SWIFT: DSHEETAA</Text>
        </View>
      </View>

      <PaymentModal />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
  },
  header: {
    padding: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
  },
  pricingContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  popularCard: {
    borderColor: '#2E7D32',
    borderWidth: 2,
    transform: [{ scale: 1.02 }],
  },
  popularBadge: {
    position: 'absolute',
    top: -12,
    left: '50%',
    marginLeft: -60,
    backgroundColor: '#2E7D32',
    paddingHorizontal: 16,
    paddingVertical: 4,
    borderRadius: 12,
  },
  popularBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  planName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    textAlign: 'center',
    marginBottom: 12,
  },
  priceContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  price: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2E7D32',
  },
  pricePeriod: {
    fontSize: 14,
    color: '#6B7280',
  },
  featuresContainer: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 12,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  checkmark: {
    color: '#2E7D32',
    marginRight: 8,
    fontSize: 14,
  },
  featureText: {
    fontSize: 13,
    color: '#6B7280',
    flex: 1,
  },
  limitsContainer: {
    marginBottom: 20,
  },
  limitText: {
    fontSize: 13,
    color: '#6B7280',
    marginBottom: 4,
  },
  limitLabel: {
    fontWeight: 'bold',
  },
  unlimitedText: {
    fontSize: 13,
    color: '#2E7D32',
    fontWeight: 'bold',
  },
  selectButton: {
    backgroundColor: '#6B7280',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  popularButton: {
    backgroundColor: '#2E7D32',
  },
  selectButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
  },
  popularButtonText: {
    color: '#FFFFFF',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    margin: 20,
    padding: 24,
    borderRadius: 12,
    width: width - 40,
    maxHeight: '80%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
    textAlign: 'center',
  },
  modalDescription: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
  },
  paymentMethodTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
  },
  paymentMethods: {
    marginBottom: 24,
  },
  paymentOption: {
    backgroundColor: '#F9FAFB',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  paymentOptionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 4,
  },
  paymentOptionDescription: {
    fontSize: 12,
    color: '#6B7280',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#6B7280',
  },
  startTrialButton: {
    backgroundColor: '#2E7D32',
  },
  cancelButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
  },
  startTrialButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
  },
  bankDetailsContainer: {
    margin: 20,
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  bankDetailsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
  },
  bankSection: {
    marginBottom: 16,
  },
  bankName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  bankInfo: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 2,
  },
});

export default PricingScreen;
